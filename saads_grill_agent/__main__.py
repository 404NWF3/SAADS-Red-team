"""Command-line entry point for adversarial repository grill assessments."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv

from saads_attack_agent.security_graph import (
    GraphConfigurationError,
    SecurityGraph,
    create_security_graph_server,
)
from saads_grill_agent.contracts import (
    AssessmentConfig,
    AssessmentState,
    Finding,
    GeneratedTestDraft,
)
from saads_grill_agent.ledger import AssessmentLedger
from saads_grill_agent.orchestrator import AssessmentOrchestrator
from saads_grill_agent.report import write_reports
from saads_grill_agent.repository import (
    RepositoryAccessError,
    RepositoryEvidenceStore,
    create_repository_server,
)
from saads_grill_agent.teams import TeamBackend, TeamTurnError
from saads_grill_agent.test_artifacts import write_test_artifact

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_REMOTE_TARGET = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*://|git@)")
_METADATA_NAME = "run_metadata.json"


@dataclass
class AssessmentRunContext:
    """Inputs shared by live and injected assessment runners."""

    command: Literal["start", "resume"]
    run_dir: Path
    config: AssessmentConfig
    store: RepositoryEvidenceStore
    ledger: AssessmentLedger
    authorization_ref: str


RunAssessmentFunction = Callable[[AssessmentRunContext], Awaitable[AssessmentState]]


class CliUsageError(ValueError):
    """User-facing argument or target validation failure."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a read-only, multi-agent adversarial review of an authorized "
            "local LLM application repository."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser(
        "start",
        help="Start a new assessment against a local target repository.",
    )
    start.add_argument(
        "target_repo",
        help="Path to an authorized local repository directory (not a URL).",
    )
    start.add_argument(
        "--authorization-ref",
        default="",
        help="Nonempty reference recording explicit review authorization.",
    )
    start.add_argument(
        "--goal",
        default=None,
        help="Optional review goal override.",
    )
    start.add_argument(
        "--profile",
        type=Path,
        default=None,
        help="Optional YAML profile overrides (supplied_* AssessmentConfig fields).",
    )
    start.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/grill_runs"),
        help="Directory that receives unique assessment run directories.",
    )
    start.add_argument(
        "--max-rounds",
        type=int,
        default=4,
        help="Maximum debate rounds per hypothesis (default: 4).",
    )
    start.add_argument(
        "--max-cost-usd",
        type=float,
        default=25.0,
        help="Global assessment cost ceiling in USD (default: 25).",
    )

    resume = subparsers.add_parser(
        "resume",
        help="Resume an interrupted assessment from its run directory.",
    )
    resume.add_argument(
        "run_dir",
        type=Path,
        help="Existing assessment run directory containing run_state.json.",
    )
    return parser


def _is_remote_target(raw: str) -> bool:
    return bool(_REMOTE_TARGET.match(raw.strip()))


def _validate_local_target(raw: str) -> Path:
    if _is_remote_target(raw):
        raise CliUsageError(
            "target must be an authorized local directory, not a URL or remote"
        )
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise CliUsageError(f"target repository is not a local directory: {raw}")
    return path


def _load_profile_overrides(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CliUsageError(f"unable to load profile: {path}") from exc
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise CliUsageError("profile YAML must be a mapping")
    allowed = {
        "supplied_model_provider",
        "supplied_model_name",
        "supplied_agent_framework",
        "supplied_frontend_roots",
        "supplied_backend_roots",
        "scope_includes",
        "scope_excludes",
        "max_threat_surfaces",
        "max_hypotheses",
        "max_agent_calls",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise CliUsageError(f"unsupported profile keys: {', '.join(unknown)}")
    return payload


def _write_run_metadata(
    run_dir: Path,
    *,
    authorization_ref: str,
    target_repo: Path,
    snapshot_id: str,
) -> None:
    payload = {
        "authorization_ref": authorization_ref,
        "target_repo": str(target_repo.resolve()),
        "snapshot_id": snapshot_id,
    }
    (run_dir / _METADATA_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read_run_metadata(run_dir: Path) -> dict[str, Any]:
    path = run_dir / _METADATA_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliUsageError(f"invalid or missing {_METADATA_NAME}") from exc
    if not isinstance(payload, dict):
        raise CliUsageError(f"invalid {_METADATA_NAME}")
    for key in ("authorization_ref", "target_repo", "snapshot_id"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CliUsageError(f"{_METADATA_NAME} missing {key}")
    return payload


def _unique_run_dir(output_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (output_root / f"{stamp}-{uuid.uuid4().hex[:8]}").resolve()


def _print_paths(run_dir: Path) -> None:
    print(str((run_dir / "run_state.json").resolve()))
    print(str((run_dir / "report.md").resolve()))


def _exit_for_state(state: AssessmentState) -> int:
    if state.phase == "complete":
        return 0
    if state.phase == "interrupted":
        return 3
    return 1


async def run_live_assessment(context: AssessmentRunContext) -> AssessmentState:
    """Build live SDK/GraphRAG dependencies and run or resume an assessment."""
    load_dotenv(PROJECT_ROOT / ".env")
    graph = SecurityGraph.load(PROJECT_ROOT)
    code_audit: list[Any] = []
    graph_audit: list[Any] = []
    mcp_servers = {
        "repository": create_repository_server(context.store, code_audit),
        "security_graph": create_security_graph_server(graph, graph_audit),
    }
    backend = TeamBackend(
        target_repo=context.config.target_repo,
        mcp_servers=mcp_servers,
    )
    orchestrator = AssessmentOrchestrator(
        backend=backend,
        evidence_store=context.store,
        ledger=context.ledger,
        security_graph=graph,
    )
    if context.command == "start":
        state = await orchestrator.run(context.config)
    else:
        state = await orchestrator.resume(context.ledger.state)

    write_reports(state, context.run_dir)
    return state


def publish_test_draft(
    context: AssessmentRunContext,
    draft: GeneratedTestDraft,
    finding: Finding | None,
) -> Path:
    """Validate and write one unexecuted test draft under the run directory."""
    if context.ledger.state.profile is None:
        raise ValueError("repository profile is required before publishing test drafts")
    return write_test_artifact(
        draft,
        finding,
        context.ledger.state.profile,
        context.run_dir,
        context.config.target_repo,
    )


def _prepare_start(args: argparse.Namespace) -> AssessmentRunContext:
    authorization_ref = (args.authorization_ref or "").strip()
    if not authorization_ref:
        raise CliUsageError("--authorization-ref is required and must be nonempty")

    target_repo = _validate_local_target(args.target_repo)
    overrides = _load_profile_overrides(args.profile)
    config_kwargs: dict[str, Any] = {
        "target_repo": target_repo,
        "max_rounds_per_hypothesis": args.max_rounds,
        "max_cost_usd": args.max_cost_usd,
        **overrides,
    }
    if args.goal is not None:
        config_kwargs["goal"] = args.goal
    try:
        config = AssessmentConfig.model_validate(config_kwargs)
    except Exception as exc:  # pydantic ValidationError
        raise CliUsageError(str(exc)) from exc

    try:
        store = RepositoryEvidenceStore.open(target_repo)
    except RepositoryAccessError as exc:
        raise CliUsageError(str(exc)) from exc

    run_dir = _unique_run_dir(Path(args.output_root))
    initial = AssessmentState(config=config, snapshot_id=store.snapshot_id)
    ledger = AssessmentLedger.create(run_dir, initial)
    _write_run_metadata(
        run_dir,
        authorization_ref=authorization_ref,
        target_repo=target_repo,
        snapshot_id=store.snapshot_id,
    )
    return AssessmentRunContext(
        command="start",
        run_dir=run_dir,
        config=config,
        store=store,
        ledger=ledger,
        authorization_ref=authorization_ref,
    )


def _prepare_resume(args: argparse.Namespace) -> AssessmentRunContext:
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        raise CliUsageError(f"run directory does not exist: {args.run_dir}")

    metadata = _read_run_metadata(run_dir)
    target_repo = _validate_local_target(metadata["target_repo"])
    try:
        store = RepositoryEvidenceStore.open(target_repo)
    except RepositoryAccessError as exc:
        raise CliUsageError(str(exc)) from exc

    if store.snapshot_id != metadata["snapshot_id"]:
        raise CliUsageError(
            "repository snapshot does not match the assessment run metadata"
        )

    try:
        ledger = AssessmentLedger.load(run_dir, expected_snapshot_id=store.snapshot_id)
    except ValueError as exc:
        raise CliUsageError(str(exc)) from exc

    # Absolute target paths are redacted from ledger checkpoints; restore exact path.
    config = ledger.state.config.model_copy(update={"target_repo": target_repo})
    ledger.state = ledger.state.model_copy(update={"config": config})

    return AssessmentRunContext(
        command="resume",
        run_dir=run_dir,
        config=config,
        store=store,
        ledger=ledger,
        authorization_ref=metadata["authorization_ref"],
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    run_assessment: RunAssessmentFunction | None = None,
) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 2

    runner = run_live_assessment if run_assessment is None else run_assessment
    try:
        if args.command == "start":
            context = _prepare_start(args)
        elif args.command == "resume":
            context = _prepare_resume(args)
        else:
            return 2
        state = asyncio.run(runner(context))
        _print_paths(context.run_dir)
        return _exit_for_state(state)
    except CliUsageError as exc:
        print(f"Usage error: {exc}", file=sys.stderr)
        return 2
    except (
        GraphConfigurationError,
        RepositoryAccessError,
        TeamTurnError,
        OSError,
        ValueError,
    ) as exc:
        print(f"Assessment failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
