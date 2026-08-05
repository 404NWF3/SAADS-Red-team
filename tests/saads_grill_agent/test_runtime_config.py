from __future__ import annotations

from pathlib import Path

import pytest

from saads_grill_agent.runtime_config import (
    load_red_team_config,
    merge_cli_over_config,
)


def test_load_defaults_when_path_missing() -> None:
    cfg = load_red_team_config(None)
    assert cfg.goal
    assert cfg.max_cost_usd == 25.0
    assert cfg.sdk.discovery_max_turns is None
    assert cfg.sdk.enable_subagents_discovery is False


def test_load_yaml_and_flat_sdk_keys(tmp_path: Path) -> None:
    path = tmp_path / "red-team-config.yaml"
    path.write_text(
        "\n".join(
            [
                "target_repo: C:/tmp/target",
                "authorization_ref: ticket-1",
                "max_cost_usd: 12.5",
                "discovery_max_turns: 80",
                "enable_subagents_discovery: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cfg = load_red_team_config(path)
    assert cfg.authorization_ref == "ticket-1"
    assert cfg.max_cost_usd == 12.5
    assert cfg.sdk.discovery_max_turns == 80
    assert cfg.sdk.enable_subagents_discovery is True


def test_cli_overrides_config_file(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yaml"
    path.write_text(
        "authorization_ref: from-file\nmax_cost_usd: 9\ngoal: from-file\n",
        encoding="utf-8",
    )
    base = load_red_team_config(path)
    merged = merge_cli_over_config(
        base,
        target_repo=str(tmp_path),
        authorization_ref="from-cli",
        goal=None,
        output_root=None,
        max_rounds=None,
        max_cost_usd=40.0,
    )
    assert merged.authorization_ref == "from-cli"
    assert merged.max_cost_usd == 40.0
    assert merged.goal == "from-file"
    assert merged.target_repo == str(tmp_path)


def test_to_assessment_config_carries_sdk(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yaml"
    path.write_text(
        "sdk:\n  team_budget_usd: 7.5\n  debate_max_turns: 30\n",
        encoding="utf-8",
    )
    cfg = load_red_team_config(path)
    assessment = cfg.to_assessment_config(tmp_path)
    assert assessment.sdk.team_budget_usd == 7.5
    assert assessment.sdk.debate_max_turns == 30


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("- not a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_red_team_config(path)
