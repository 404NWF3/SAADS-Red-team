from __future__ import annotations

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = PROJECT_ROOT / ".claude" / "skills"
PURPOSES = (
    "intent_classification",
    "case_grounding",
    "script_grounding",
)


@pytest.mark.parametrize(
    ("name", "purpose"),
    [
        ("recognize-attack-intent", "intent_classification"),
        ("ground-attack-case", "case_grounding"),
        ("generate-offline-attack-script", "script_grounding"),
    ],
)
def test_project_skill_is_discoverable_and_declares_one_graph_purpose(
    name: str,
    purpose: str,
) -> None:
    skill_dir = SKILLS_ROOT / name
    document = skill_dir.joinpath("SKILL.md").read_text(encoding="utf-8")
    parts = document.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2]
    metadata = yaml.safe_load(
        skill_dir.joinpath("agents", "openai.yaml").read_text(encoding="utf-8")
    )

    assert frontmatter["name"] == name
    assert set(frontmatter) == {"name", "description"}
    assert metadata["interface"]["display_name"]
    assert f"${name}" in metadata["interface"]["default_prompt"]
    assert "mcp__security_graph__query_security_graph" in body
    assert f"purpose={purpose}" in body
    for other_purpose in set(PURPOSES) - {purpose}:
        assert f"purpose={other_purpose}" not in body
    assert "offline" in body.lower()
