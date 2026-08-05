from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = PROJECT_ROOT / ".claude" / "skills" / "ground-red-team-evidence" / "SKILL.md"


def test_ground_red_team_evidence_skill_exists_with_matching_frontmatter() -> None:
    assert SKILL_PATH.is_file()
    document = SKILL_PATH.read_text(encoding="utf-8")
    parts = document.split("---", 2)
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2]

    assert frontmatter["name"] == "ground-red-team-evidence"
    assert "GraphRAG" in frontmatter["description"] or "graph" in frontmatter["description"].lower()
    assert "mcp__security_graph__query_security_graph" in body
    assert "threat_modeling" in body
    assert "hypothesis_grounding" in body
    assert "adjudication_grounding" in body
    assert "test_grounding" in body
    assert "evidence_id" in body
