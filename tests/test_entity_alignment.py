import asyncio
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from llm_defense_graphrag.entity_alignment import (
    AlignmentDecision,
    AlignmentError,
    EntityCandidate,
    GlmAlignmentResponse,
    GlmAmbiguityResolver,
    align_graph_tables,
    load_entity_registry,
)


def test_registry_resolves_observed_entity_variants() -> None:
    registry = load_entity_registry(Path("config/entity_aliases.yaml"))

    cases = [
        ("AI BOM", "DEFENSE_CONTROL", "AIBOM", "DEFENSE_CONTROL"),
        ("AIBOM", "COMPONENT", "AIBOM", "DEFENSE_CONTROL"),
        ("HUGGINGFACE", "COMPONENT", "HUGGING FACE", "COMPONENT"),
        (
            "LARGE LANGUAGE MODEL (LLM)",
            "COMPONENT",
            "LLM",
            "COMPONENT",
        ),
        (
            "FINE-TUNING",
            "COMPONENT",
            "FINE TUNING PIPELINE",
            "COMPONENT",
        ),
        (
            "FINETUNING",
            "ATTACK_TECHNIQUE",
            "FINE TUNING PIPELINE",
            "COMPONENT",
        ),
        ("ENSEMBLE", "EVALUATION", "ENSEMBLE", "COMPONENT"),
        (
            "PROMPT ENGINEERING",
            "ATTACK_TECHNIQUE",
            "PROMPT ENGINEERING",
            "DEFENSE_CONTROL",
        ),
        (
            "MACHINE UNLEARNING",
            "ATTACK_TECHNIQUE",
            "MACHINE UNLEARNING",
            "DEFENSE_CONTROL",
        ),
        ("QUANTIZATION", "VULNERABILITY", "QUANTIZATION", "COMPONENT"),
        (
            "REINFORCEMENT LEARNING",
            "DEFENSE_CONTROL",
            "REINFORCEMENT LEARNING",
            "COMPONENT",
        ),
        (
            "SUPERVISED FINE-TUNING",
            "ATTACK_TECHNIQUE",
            "SUPERVISED FINE TUNING",
            "COMPONENT",
        ),
    ]

    for title, entity_type, expected_title, expected_type in cases:
        decision = registry.resolve(title, entity_type)
        assert decision is not None
        assert (decision.canonical_title, decision.canonical_type) == (
            expected_title,
            expected_type,
        )


def test_align_graph_tables_merges_aliases_and_remaps_relationships() -> None:
    entities = pd.DataFrame(
        [
            {
                "title": "AI BOM",
                "type": "DEFENSE_CONTROL",
                "description": "Supply-chain control.",
                "text_unit_ids": ["u1"],
                "frequency": 1,
            },
            {
                "title": "AIBOM",
                "type": "COMPONENT",
                "description": "Artifact inventory.",
                "text_unit_ids": ["u2"],
                "frequency": 2,
            },
            {
                "title": "LLM",
                "type": "COMPONENT",
                "description": "Language model.",
                "text_unit_ids": ["u1"],
                "frequency": 1,
            },
            {
                "title": "LARGE LANGUAGE MODEL (LLM)",
                "type": "COMPONENT",
                "description": "Expanded language model name.",
                "text_unit_ids": ["u2"],
                "frequency": 1,
            },
        ]
    )
    relationships = pd.DataFrame(
        [
            {
                "source": "AI BOM",
                "target": "LLM",
                "description": "Control protects model.",
                "text_unit_ids": ["u1"],
                "weight": 7.0,
            },
            {
                "source": "AIBOM",
                "target": "LARGE LANGUAGE MODEL (LLM)",
                "description": "Inventory covers model.",
                "text_unit_ids": ["u2"],
                "weight": 3.0,
            },
            {
                "source": "AI BOM",
                "target": "AIBOM",
                "description": "Alias-only edge.",
                "text_unit_ids": ["u3"],
                "weight": 2.0,
            },
        ]
    )

    result = asyncio.run(
        align_graph_tables(
            entities,
            relationships,
            load_entity_registry(Path("config/entity_aliases.yaml")),
        )
    )

    assert result.entities["title"].tolist() == ["AIBOM", "LLM"]
    aibom = result.entities.set_index("title").loc["AIBOM"]
    assert aibom["type"] == "DEFENSE_CONTROL"
    assert aibom["frequency"] == 3
    assert aibom["text_unit_ids"] == ["u1", "u2"]
    assert aibom["description"] == "Supply-chain control.\n\nArtifact inventory."

    assert len(result.relationships) == 1
    edge = result.relationships.iloc[0]
    assert (edge["source"], edge["target"]) == ("AIBOM", "LLM")
    assert edge["weight"] == 10.0
    assert edge["text_unit_ids"] == ["u1", "u2"]
    assert edge["description"] == (
        "Control protects model.\n\nInventory covers model."
    )
    assert set(result.relationships["source"]).union(
        result.relationships["target"]
    ) <= set(result.entities["title"])
    assert len(result.audit) == len(entities)


def test_glm_resolver_uses_structured_graphrag_completion() -> None:
    requests: list[dict[str, object]] = []

    class FakeCompletion:
        async def completion_async(self, **kwargs: object) -> SimpleNamespace:
            requests.append(kwargs)
            return SimpleNamespace(
                formatted_response=GlmAlignmentResponse.model_validate(
                    {
                        "canonical_title": "EXAMPLE NAME",
                        "canonical_type": "COMPONENT",
                        "confidence": 0.96,
                        "reason": "Equivalent spelling",
                    }
                )
            )

    resolver = GlmAmbiguityResolver(FakeCompletion())
    decisions = asyncio.run(
        resolver.resolve(
            [
                EntityCandidate(
                    title="EXAMPLE-NAME",
                    entity_type="COMPONENT",
                    description="A sample component.",
                ),
                EntityCandidate(
                    title="EXAMPLE NAME",
                    entity_type="COMPONENT",
                    description="The same component.",
                ),
            ]
        )
    )

    assert len(decisions) == 2
    assert (
        decisions[0].canonical_title,
        decisions[0].canonical_type,
        decisions[0].method,
        decisions[0].confidence,
    ) == ("EXAMPLE NAME", "COMPONENT", "glm", 0.96)
    assert requests[0]["response_format"] is GlmAlignmentResponse
    assert requests[0]["temperature"] == 0
    prompt = requests[0]["messages"][0]["content"]
    assert '"canonical_title"' in prompt
    assert '"canonical_type"' in prompt
    assert '"confidence"' in prompt


def test_glm_resolver_keeps_low_confidence_decision_for_review() -> None:
    class FakeCompletion:
        async def completion_async(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                formatted_response=GlmAlignmentResponse.model_validate(
                    {
                        "canonical_title": "EXAMPLE NAME",
                        "canonical_type": "COMPONENT",
                        "confidence": 0.89,
                        "reason": "Uncertain spelling",
                    }
                )
            )

    decisions = asyncio.run(
        GlmAmbiguityResolver(FakeCompletion()).resolve(
            [
                EntityCandidate(
                    title="EXAMPLE-NAME",
                    entity_type="COMPONENT",
                    description="A sample component.",
                ),
                EntityCandidate(
                    title="EXAMPLE NAME",
                    entity_type="COMPONENT",
                    description="The same component.",
                ),
            ]
        )
    )

    assert decisions[0].canonical_title == "EXAMPLE-NAME"
    assert decisions[0].method == "glm_review_required"


def test_glm_resolver_retries_once_after_structured_validation_failure() -> None:
    class FakeCompletion:
        def __init__(self) -> None:
            self.calls = 0

        async def completion_async(self, **_kwargs: object) -> SimpleNamespace:
            self.calls += 1
            if self.calls == 1:
                GlmAlignmentResponse.model_validate(
                    {"candidates": ["echoed input"]}
                )
            return SimpleNamespace(
                formatted_response=GlmAlignmentResponse.model_validate(
                    {
                        "canonical_title": "EXAMPLE NAME",
                        "canonical_type": "COMPONENT",
                        "confidence": 0.97,
                        "reason": "Equivalent spelling",
                    }
                )
            )

    completion = FakeCompletion()
    decisions = asyncio.run(
        GlmAmbiguityResolver(completion).resolve(
            [
                EntityCandidate("EXAMPLE-NAME", "COMPONENT", "First spelling."),
                EntityCandidate("EXAMPLE NAME", "COMPONENT", "Second spelling."),
            ]
        )
    )

    assert completion.calls == 2
    assert {decision.canonical_title for decision in decisions} == {
        "EXAMPLE NAME"
    }


def test_glm_resolver_rejects_missing_structured_response() -> None:
    class FakeCompletion:
        async def completion_async(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(formatted_response=None)

    with pytest.raises(AlignmentError, match="structured response"):
        asyncio.run(
            GlmAmbiguityResolver(FakeCompletion()).resolve(
                [
                    EntityCandidate(
                        title="EXAMPLE-NAME",
                        entity_type="COMPONENT",
                        description="A sample component.",
                    ),
                    EntityCandidate(
                        title="EXAMPLE NAME",
                        entity_type="COMPONENT",
                        description="The same component.",
                    ),
                ]
            )
        )


def test_align_graph_tables_sends_unresolved_lexical_group_to_resolver() -> None:
    class FakeResolver:
        async def resolve(
            self, candidates: list[EntityCandidate]
        ) -> list[AlignmentDecision]:
            return [
                AlignmentDecision(
                    source_title=candidate.title,
                    source_type=candidate.entity_type,
                    canonical_title="EXAMPLE NAME",
                    canonical_type="COMPONENT",
                    method="glm",
                    confidence=0.98,
                    reason="Equivalent spelling",
                )
                for candidate in candidates
            ]

    entities = pd.DataFrame(
        [
            {
                "title": "EXAMPLE-NAME",
                "type": "COMPONENT",
                "description": "First spelling.",
                "text_unit_ids": ["u1"],
                "frequency": 1,
            },
            {
                "title": "EXAMPLE NAME",
                "type": "COMPONENT",
                "description": "Second spelling.",
                "text_unit_ids": ["u2"],
                "frequency": 1,
            },
        ]
    )
    relationships = pd.DataFrame(
        columns=["source", "target", "description", "text_unit_ids", "weight"]
    )

    result = asyncio.run(
        align_graph_tables(
            entities,
            relationships,
            load_entity_registry(Path("config/entity_aliases.yaml")),
            resolver=FakeResolver(),
        )
    )

    assert result.entities["title"].tolist() == ["EXAMPLE NAME"]
    assert result.entities.iloc[0]["frequency"] == 2
    assert result.audit["method"].tolist() == ["glm", "glm"]
