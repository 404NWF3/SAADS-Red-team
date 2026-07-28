from __future__ import annotations

from pathlib import Path

import pytest

from saads_attack_agent.agent import (
    AgentConfigurationError,
    UnsupportedAttackIntent,
)
from saads_attack_agent.__main__ import main
from saads_attack_agent.contracts import GeneratedAttackPackage
from tests.saads_attack_agent.test_artifacts import valid_package


async def fake_generate_valid_package(
    _request: str,
) -> GeneratedAttackPackage:
    return valid_package()


def test_cli_prints_the_two_created_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["RAG prompt injection", "--output-root", str(tmp_path)],
        generate=fake_generate_valid_package,
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert str((tmp_path / "case-001" / "attack_case.json").resolve()) in output
    assert str((tmp_path / "case-001" / "attack.py").resolve()) in output


def test_cli_returns_two_for_unsupported_intent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def unsupported(_request: str) -> GeneratedAttackPackage:
        raise UnsupportedAttackIntent("No supported family")

    exit_code = main(
        ["model extraction", "--output-root", str(tmp_path)],
        generate=unsupported,
    )

    assert exit_code == 2
    assert "Unsupported attack intent" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_cli_returns_one_for_missing_configuration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def missing_config(_request: str) -> GeneratedAttackPackage:
        raise AgentConfigurationError("DEEPSEEK_API_KEY is required")

    exit_code = main(
        ["RAG prompt injection", "--output-root", str(tmp_path)],
        generate=missing_config,
    )

    assert exit_code == 1
    assert "DEEPSEEK_API_KEY is required" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
