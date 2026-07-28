"""Command-line entry point for offline attack case generation."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path

from dotenv import load_dotenv

from saads_attack_agent.agent import (
    AttackAgentError,
    AttackCaseAgent,
    ClaudeAgentBackend,
    UnsupportedAttackIntent,
)
from saads_attack_agent.artifacts import (
    ArtifactValidationError,
    write_attack_package,
)
from saads_attack_agent.contracts import GeneratedAttackPackage
from saads_attack_agent.security_graph import (
    GraphConfigurationError,
    SecurityGraph,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GenerateFunction = Callable[[str], Awaitable[GeneratedAttackPackage]]


async def generate_live_package(request: str) -> GeneratedAttackPackage:
    """Build the real SDK and GraphRAG dependencies for one request."""
    load_dotenv(PROJECT_ROOT / ".env")
    graph = SecurityGraph.load(PROJECT_ROOT)
    backend = ClaudeAgentBackend(
        project_root=PROJECT_ROOT,
        graph=graph,
    )
    return await AttackCaseAgent(backend).generate(request)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate one GraphRAG-grounded LLM attack case and an "
            "offline-only Python simulation."
        )
    )
    parser.add_argument(
        "request",
        help=(
            "Free-text request for prompt injection, long-horizon dialogue, "
            "or tool hijack."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("artifacts/attack_cases"),
        help="Directory that receives the generated case directory.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    generate: GenerateFunction | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    generator = generate_live_package if generate is None else generate
    try:
        package = asyncio.run(generator(args.request))
        paths = write_attack_package(package, args.output_root)
    except UnsupportedAttackIntent as exc:
        print(f"Unsupported attack intent: {exc}", file=sys.stderr)
        return 2
    except (
        AttackAgentError,
        ArtifactValidationError,
        GraphConfigurationError,
        OSError,
        ValueError,
    ) as exc:
        print(f"Attack case generation failed: {exc}", file=sys.stderr)
        return 1

    print(paths.case_json.resolve())
    print(paths.script.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
