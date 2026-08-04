from __future__ import annotations

import json
from pathlib import Path

import pytest

from saads_grill_agent.__main__ import AssessmentRunContext, main
from saads_grill_agent.contracts import AssessmentState
from saads_grill_agent.report import write_reports


def fixture_repo() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "vulnerable_llm_app"


async def fake_completed_assessment(
    context: AssessmentRunContext,
) -> AssessmentState:
    state = AssessmentState(
        config=context.config,
        snapshot_id=context.store.snapshot_id,
        phase="complete",
        team_sessions=dict(context.ledger.state.team_sessions),
        agent_calls_used=context.ledger.state.agent_calls_used,
        cost_usd_used=context.ledger.state.cost_usd_used,
        evidence_ids=list(context.ledger.state.evidence_ids),
        hypotheses=dict(context.ledger.state.hypotheses),
        findings=list(context.ledger.state.findings),
        profile=context.ledger.state.profile,
        threat_surfaces=list(context.ledger.state.threat_surfaces),
        discovery=context.ledger.state.discovery,
    )
    context.ledger.checkpoint(state)
    write_reports(state, context.run_dir)
    return state


async def fake_interrupted_assessment(
    context: AssessmentRunContext,
) -> AssessmentState:
    state = AssessmentState(
        config=context.config,
        snapshot_id=context.store.snapshot_id,
        phase="interrupted",
        cost_usd_used=context.config.max_cost_usd,
    )
    context.ledger.checkpoint(state)
    write_reports(state, context.run_dir)
    return state


async def fake_budget_exceeded_assessment(
    context: AssessmentRunContext,
) -> AssessmentState:
    state = AssessmentState(
        config=context.config,
        snapshot_id=context.store.snapshot_id,
        phase="interrupted",
        cost_usd_used=context.config.max_cost_usd,
        agent_calls_used=1,
    )
    context.ledger.checkpoint(state)
    write_reports(state, context.run_dir)
    return state


def test_start_prints_run_and_report_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(
        [
            "start",
            str(fixture_repo()),
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
        ],
        run_assessment=fake_completed_assessment,
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "run_state.json" in output
    assert "report.md" in output


def test_start_requires_explicit_local_repository(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(
        [
            "start",
            "https://example.test/repo.git",
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
        ]
    )
    assert exit_code == 2
    err = capsys.readouterr().err.lower()
    assert "url" in err or "remote" in err


def test_fixture_debug_exposes_assembled_system_prompt() -> None:
    """Offline seed check: debug helper returns the assembled system prompt."""
    import sys

    root = fixture_repo()
    inserted = str(root)
    sys.path.insert(0, inserted)
    stale = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for name in stale:
        del sys.modules[name]
    try:
        from app.debug import assembled_system_prompt_for_debug
        from app.prompts import TRUSTED_SYSTEM_PROMPT

        prompt = assembled_system_prompt_for_debug("revenue")
        assert TRUSTED_SYSTEM_PROMPT in prompt
        assert "Additional context:" in prompt
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]

    main_py = (root / "app" / "main.py").read_text(encoding="utf-8")
    assert "/debug/system-prompt" in main_py
    assert "assembled_system_prompt_for_debug" in main_py


def test_start_requires_nonempty_authorization_ref(tmp_path: Path) -> None:
    assert (
        main(
            [
                "start",
                str(fixture_repo()),
                "--authorization-ref",
                "   ",
                "--output-root",
                str(tmp_path),
            ]
        )
        == 2
    )


def test_start_records_authorization_ref(tmp_path: Path) -> None:
    exit_code = main(
        [
            "start",
            str(fixture_repo()),
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
        ],
        run_assessment=fake_completed_assessment,
    )
    assert exit_code == 0
    run_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    metadata = json.loads((run_dirs[0] / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["authorization_ref"] == "fixture-test"
    assert metadata["target_repo"] == str(fixture_repo().resolve())


def test_resume_reloads_run_and_prints_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    start_code = main(
        [
            "start",
            str(fixture_repo()),
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
        ],
        run_assessment=fake_interrupted_assessment,
    )
    assert start_code == 3
    run_dir = next(path for path in tmp_path.iterdir() if path.is_dir())

    resume_code = main(
        ["resume", str(run_dir)],
        run_assessment=fake_completed_assessment,
    )
    assert resume_code == 0
    output = capsys.readouterr().out
    assert "run_state.json" in output
    assert "report.md" in output
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    assert state["phase"] == "complete"


def test_resume_fails_closed_on_snapshot_mismatch(tmp_path: Path) -> None:
    start_code = main(
        [
            "start",
            str(fixture_repo()),
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
        ],
        run_assessment=fake_interrupted_assessment,
    )
    assert start_code == 3
    run_dir = next(path for path in tmp_path.iterdir() if path.is_dir())
    metadata_path = run_dir / "run_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["snapshot_id"] = "snap-tampered-mismatch"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    assert main(["resume", str(run_dir)], run_assessment=fake_completed_assessment) == 2


def test_budget_exceeded_exits_with_interrupted_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(
        [
            "start",
            str(fixture_repo()),
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
            "--max-cost-usd",
            "1",
        ],
        run_assessment=fake_budget_exceeded_assessment,
    )
    assert exit_code == 3
    output = capsys.readouterr().out
    assert "run_state.json" in output
    assert "report.md" in output
    run_dir = next(path for path in tmp_path.iterdir() if path.is_dir())
    state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    assert state["phase"] == "interrupted"
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "report.md").stat().st_size > 0


def test_interrupted_report_exit_case(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(
        [
            "start",
            str(fixture_repo()),
            "--authorization-ref",
            "fixture-test",
            "--output-root",
            str(tmp_path),
        ],
        run_assessment=fake_interrupted_assessment,
    )
    assert exit_code == 3
    output = capsys.readouterr().out
    assert "run_state.json" in output
    assert "report.md" in output
