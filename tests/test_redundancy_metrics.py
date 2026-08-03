from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.evaluate_redundancy import (
    canonical_title,
    combined_entity_redundancy,
    embedding_entity_redundancy,
    lexical_entity_redundancy,
    relation_redundancy,
)


def test_canonical_title_strips_spaces_and_hyphens() -> None:
    assert canonical_title("HUGGING FACE") == "HUGGINGFACE"
    assert canonical_title("FINE-TUNING") == "FINETUNING"
    assert canonical_title("AI BOM") == "AIBOM"


def test_lexical_entity_redundancy_groups_format_variants() -> None:
    entities = pd.DataFrame(
        [
            {"title": "HUGGING FACE", "type": "COMPONENT"},
            {"title": "HUGGINGFACE", "type": "COMPONENT"},
            {"title": "LLM", "type": "COMPONENT"},
            {"title": "PROMPT INJECTION", "type": "ATTACK_TECHNIQUE"},
        ]
    )
    metrics = lexical_entity_redundancy(entities, sample_limit=10)
    assert metrics["entity_count"] == 4
    assert metrics["redundant_entity_count"] == 2
    assert metrics["entity_redundancy_rate"] == 0.5
    assert metrics["multi_member_cluster_count"] == 1


def test_embedding_entity_redundancy_clusters_similar_vectors() -> None:
    entities = pd.DataFrame(
        [
            {"title": "LLM", "type": "COMPONENT"},
            {"title": "LARGE LANGUAGE MODEL (LLM)", "type": "COMPONENT"},
            {"title": "VECTOR STORE", "type": "COMPONENT"},
            {"title": "PROMPT INJECTION", "type": "ATTACK_TECHNIQUE"},
        ]
    )
    vectors = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.99, 0.01, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    metrics = embedding_entity_redundancy(
        entities, vectors, cosine_threshold=0.85, sample_limit=10
    )
    assert metrics["redundant_entity_count"] == 2
    assert metrics["entity_redundancy_rate"] == 0.5
    assert any(
        set(sample["titles"]) == {"LLM", "LARGE LANGUAGE MODEL (LLM)"}
        for sample in metrics["cluster_samples"]
    )


def test_combined_includes_lexical_and_embedding_links() -> None:
    entities = pd.DataFrame(
        [
            {"title": "AI BOM", "type": "COMPONENT"},
            {"title": "AIBOM", "type": "COMPONENT"},
            {"title": "LLM", "type": "COMPONENT"},
            {"title": "LARGE LANGUAGE MODEL (LLM)", "type": "COMPONENT"},
        ]
    )
    vectors = np.asarray(
        [
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],  # lexical-only pair; vectors dissimilar
            [1.0, 0.0, 0.0],
            [0.99, 0.01, 0.0],  # embedding-only pair
        ],
        dtype=np.float32,
    )
    lexical = lexical_entity_redundancy(entities, sample_limit=10)
    embedding = embedding_entity_redundancy(
        entities, vectors, cosine_threshold=0.85, sample_limit=10
    )
    combined = combined_entity_redundancy(
        entities, vectors, cosine_threshold=0.85, sample_limit=10
    )
    assert lexical["redundant_entity_count"] == 2
    assert embedding["redundant_entity_count"] == 2
    assert combined["redundant_entity_count"] == 4
    assert combined["entity_redundancy_rate"] == 1.0


def test_relation_redundancy_counts_self_loops_and_duplicate_extras() -> None:
    relationships = pd.DataFrame(
        [
            {"source": "A", "target": "B", "description": "a targets b"},
            {"source": "A", "target": "B", "description": "a also targets b"},
            {"source": "C", "target": "C", "description": "self loop"},
            {"source": "D", "target": "E", "description": "unique"},
        ]
    )
    metrics = relation_redundancy(relationships, sample_limit=10)
    assert metrics["relationship_count"] == 4
    assert metrics["self_loop_count"] == 1
    assert metrics["duplicate_pair_count"] == 1
    assert metrics["duplicate_extra_count"] == 1
    assert metrics["conflicting_pair_count"] == 1
    assert metrics["redundant_relationship_count"] == 2
    assert metrics["relation_redundancy_rate"] == 0.5
