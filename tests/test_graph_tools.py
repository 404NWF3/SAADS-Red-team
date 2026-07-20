from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

from scripts.analyze_graph import (
    attack_defense_coverage,
    canonical_title,
    degree_stats,
    relationship_quality,
)
from scripts.evaluate_queries import select_questions


def test_evaluation_set_has_ten_questions_per_method() -> None:
    data = yaml.safe_load(Path("eval/questions.yaml").read_text(encoding="utf-8"))
    questions = data["questions"]

    assert len(questions) == 40
    assert len({item["id"] for item in questions}) == 40
    assert Counter(item["method"] for item in questions) == {
        "basic": 10,
        "local": 10,
        "global": 10,
        "drift": 10,
    }
    assert len(select_questions(questions, smoke=True, question_ids=[])) == 4


def test_graph_quality_helpers_preserve_attack_defense_direction() -> None:
    entities = pd.DataFrame(
        [
            {"title": "PROMPT INJECTION", "type": "ATTACK_TECHNIQUE"},
            {"title": "TOOL CALL VALIDATION", "type": "DEFENSE_CONTROL"},
            {"title": "TOOL EXECUTOR", "type": "COMPONENT"},
        ]
    )
    relationships = pd.DataFrame(
        [
            {
                "source": "TOOL CALL VALIDATION",
                "target": "PROMPT INJECTION",
                "description": "该控制缓解 prompt injection。",
            },
            {
                "source": "PROMPT INJECTION",
                "target": "TOOL EXECUTOR",
                "description": "该攻击针对 tool executor。",
            },
        ]
    )

    semantics, anomalies = relationship_quality(entities, relationships)
    degree = degree_stats(entities, relationships)
    coverage = attack_defense_coverage(entities, relationships)

    assert canonical_title("Tool-call validation") == "TOOLCALLVALIDATION"
    assert semantics["mitigates"] == 1
    assert semantics["targets"] == 1
    assert anomalies == []
    assert degree["isolated_count"] == 0
    assert coverage["coverage_ratio"] == 1.0
