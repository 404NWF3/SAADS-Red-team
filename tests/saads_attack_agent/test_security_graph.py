from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

import saads_attack_agent.security_graph as security_graph_module
from saads_attack_agent.contracts import GraphEvidence
from saads_attack_agent.security_graph import (
    GraphConfigurationError,
    LoadedGraph,
    SecurityGraph,
    create_security_graph_server,
)


def loaded_graph_fixture() -> LoadedGraph:
    return LoadedGraph(
        config="config",
        entities="entities",
        communities="communities",
        community_reports="community_reports",
        text_units="text_units",
        relationships="relationships",
    )


class FakeLocalSearch:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls: list[dict[str, Any]] = []

    async def __call__(self, **kwargs: Any) -> tuple[str, str]:
        self.calls.append(kwargs)
        return self.answer, "context"


def test_query_returns_stable_evidence_from_graph_answer(
    tmp_path: Path,
) -> None:
    search = FakeLocalSearch("Grounded answer [Data: Entities (1)].")
    graph = SecurityGraph(
        root=tmp_path,
        loaded=loaded_graph_fixture(),
        search=search,
    )

    first = asyncio.run(
        graph.query(
            "intent_classification",
            "Classify indirect prompt injection.",
        )
    )
    second = asyncio.run(
        graph.query(
            "intent_classification",
            "Classify indirect prompt injection.",
        )
    )

    assert first == second
    assert first.answer == "Grounded answer [Data: Entities (1)]."
    assert first.evidence_id == "intent_classification-851def28d835"
    assert search.calls[0] == {
        "config": "config",
        "entities": "entities",
        "communities": "communities",
        "community_reports": "community_reports",
        "text_units": "text_units",
        "relationships": "relationships",
        "covariates": None,
        "community_level": 2,
        "response_type": "Multiple Paragraphs with source citations",
        "query": "Classify indirect prompt injection.",
    }


def test_load_fails_before_query_when_graph_tables_are_missing(
    tmp_path: Path,
) -> None:
    with pytest.raises(GraphConfigurationError, match="entities.parquet"):
        SecurityGraph.load(tmp_path)


def test_sdk_tool_returns_structured_evidence_and_appends_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}

    def capture_server(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"captured": True}

    monkeypatch.setattr(
        security_graph_module,
        "create_sdk_mcp_server",
        capture_server,
    )
    graph = SecurityGraph(
        root=tmp_path,
        loaded=loaded_graph_fixture(),
        search=FakeLocalSearch("Grounded tool answer."),
    )
    audit: list[GraphEvidence] = []

    server = create_security_graph_server(graph, audit)
    tool = captured["tools"][0]
    response = asyncio.run(
        tool.handler(
            {
                "purpose": "case_grounding",
                "question": "Ground an offline prompt injection case.",
            }
        )
    )

    assert server == {"captured": True}
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.idempotentHint is True
    assert response["structuredContent"] == audit[0].model_dump(mode="json")
    assert response["content"][0]["text"] == "Grounded tool answer."
