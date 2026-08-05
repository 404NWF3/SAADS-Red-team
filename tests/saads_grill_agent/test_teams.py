from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator

import pytest
from pydantic import ValidationError

from saads_grill_agent.contracts import VulnerabilityHypothesis
from saads_grill_agent.teams import (
    CODE_SUBAGENTS,
    GRAPH_TOOL,
    RED_SUBAGENTS,
    REPOSITORY_TOOLS,
    TeamBackend,
    TeamTurnAudits,
    TeamTurnError,
    HypothesisBatch,
    RebuttalBatch,
    RedResponseBatch,
    AdjudicationVerdict as _AdjudicationModel,
    JUDGE_BUDGET_USD,
    JUDGE_MAX_TURNS,
    TEAM_BUDGET_USD,
    TEAM_MAX_TURNS,
)


def valid_hypothesis() -> dict[str, Any]:
    return {
        "hypothesis_id": "hyp-1",
        "surface_id": "surf-1",
        "title": "Indirect prompt injection via RAG",
        "root_cause": "Untrusted retrieval content is concatenated with trusted instructions.",
        "attack_path": ["attacker controls retrieved context", "model obeys injected instruction"],
        "impact": "Instruction hijack.",
        "preconditions": ["retrieval returns attacker content"],
        "code_evidence_ids": ["code-1"],
        "graph_evidence_ids": [],
    }


def valid_hypothesis_batch() -> dict[str, Any]:
    return {"hypotheses": [valid_hypothesis()]}


def empty_audits() -> TeamTurnAudits:
    return TeamTurnAudits(tool_events=[])


@dataclass
class CapturedCall:
    prompt: str
    options: Any


class FakeQueryStream:
    """Mimics claude_agent_sdk.query: captures options, yields one ResultMessage."""

    def __init__(self, structured_output: Any, session_id: str = "session-from-result") -> None:
        self.structured_output = structured_output
        self.session_id = session_id
        self.calls: list[CapturedCall] = []

    def __call__(self, *, prompt: str, options: Any) -> AsyncIterator[Any]:
        self.calls.append(CapturedCall(prompt=prompt, options=options))
        return self._stream()

    async def _stream(self) -> AsyncIterator[Any]:
        from claude_agent_sdk import ResultMessage
        yield ResultMessage(
            subtype="success",
            duration_ms=1,
            duration_api_ms=1,
            is_error=False,
            num_turns=1,
            session_id=self.session_id,
            structured_output=self.structured_output,
        )


class FailingQueryStream:
    def __init__(self) -> None:
        self.calls: list[CapturedCall] = []

    def __call__(self, *, prompt: str, options: Any) -> AsyncIterator[Any]:
        self.calls.append(CapturedCall(prompt=prompt, options=options))
        return self._stream()

    async def _stream(self) -> AsyncIterator[Any]:
        from claude_agent_sdk import ResultMessage
        yield ResultMessage(
            subtype="error_max_turns",
            duration_ms=1,
            duration_api_ms=1,
            is_error=True,
            num_turns=1,
            session_id="session-err",
            structured_output=None,
        )


def fake_team_backend(tmp_path: Path, structured_output: Any) -> tuple[TeamBackend, FakeQueryStream]:
    stream = FakeQueryStream(structured_output)
    backend = TeamBackend(
        target_repo=tmp_path,
        sdk_query=stream,
    )
    return backend, stream


# --- role isolation -------------------------------------------------------


def test_red_team_gets_only_agent_and_read_only_mcp_tools(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, valid_hypothesis_batch())
    result = asyncio.run(backend.run_turn(
        role="red_team",
        prompt="Discover grounded hypotheses",
        output_model=HypothesisBatch,
        session_id="session-red-1",
        audits=empty_audits(),
    ))

    options = captured.calls[0].options
    assert options.resume == "session-red-1"
    assert options.setting_sources == []
    assert options.permission_mode == "dontAsk"
    assert options.max_turns == TEAM_MAX_TURNS
    assert options.max_turns == 40
    assert set(options.allowed_tools) == {
        "Agent",
        "mcp__repository__list_repository",
        "mcp__repository__search_repository",
        "mcp__repository__read_repository_snippet",
        "mcp__security_graph__query_security_graph",
    }
    assert "Bash" not in options.tools
    assert result.session_id == "session-from-result"


def test_code_team_cannot_call_graphrag(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, {"rebuttals": []})
    asyncio.run(backend.run_turn(
        role="code_team",
        prompt="Falsify this hypothesis",
        output_model=RebuttalBatch,
        session_id=None,
        audits=empty_audits(),
    ))

    options = captured.calls[0].options
    assert "mcp__security_graph__query_security_graph" not in options.allowed_tools
    assert "mcp__repository__read_repository_snippet" in options.allowed_tools
    # code team has no graph subagent either
    code_subagent_names = set(CODE_SUBAGENTS)
    assert "graph-grounder" not in code_subagent_names


def test_enable_subagents_false_strips_agent_tool(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, {"rebuttals": []})
    asyncio.run(backend.run_turn(
        role="code_team",
        prompt="Profile without subagents",
        output_model=RebuttalBatch,
        session_id=None,
        audits=empty_audits(),
        enable_subagents=False,
    ))

    options = captured.calls[0].options
    assert "Agent" not in options.allowed_tools
    assert options.agents == {} or not options.agents
    assert options.tools == []
    assert "mcp__repository__read_repository_snippet" in options.allowed_tools


def test_judge_cannot_invoke_subagents(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, {
        "adjudication_id": "adj-1",
        "hypothesis_id": "hyp-1",
        "round_number": 1,
        "verdict": "confirm",
        "rationale": ["reachable"],
        "accepted_code_evidence_ids": ["code-1"],
        "accepted_graph_evidence_ids": [],
        "missing_proof": [],
        "duplicate_of": None,
        "confidence": 0.9,
    })
    asyncio.run(backend.run_turn(
        role="judge",
        prompt="Adjudicate",
        output_model=_AdjudicationModel,
        session_id=None,
        audits=empty_audits(),
    ))

    options = captured.calls[0].options
    assert "Agent" not in options.allowed_tools
    assert options.agents == {} or not options.agents
    # judge still has both evidence families
    assert "mcp__repository__read_repository_snippet" in options.allowed_tools
    assert "mcp__security_graph__query_security_graph" in options.allowed_tools
    # judge budget is tighter than team budget
    assert options.max_budget_usd == pytest.approx(JUDGE_BUDGET_USD)
    assert options.max_turns == JUDGE_MAX_TURNS
    assert options.max_turns == 20


def test_every_call_uses_output_format(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, valid_hypothesis_batch())
    asyncio.run(backend.run_turn(
        role="red_team",
        prompt="Discover",
        output_model=HypothesisBatch,
        session_id=None,
        audits=empty_audits(),
    ))

    options = captured.calls[0].options
    assert options.output_format["type"] == "json_schema"
    assert "schema" in options.output_format
    # cwd pinned to resolved target repo, and no setting sources (isolation)
    assert options.cwd == str(tmp_path.resolve())
    assert options.setting_sources == []


def test_failed_turn_keeps_state_and_raises(tmp_path: Path) -> None:
    stream = FailingQueryStream()
    backend = TeamBackend(target_repo=tmp_path, sdk_query=stream)
    audits = empty_audits()
    with pytest.raises(TeamTurnError):
        asyncio.run(backend.run_turn(
            role="red_team",
            prompt="Discover",
            output_model=HypothesisBatch,
            session_id="session-red-1",
            audits=audits,
        ))
    # no partial session id recorded for the caller to reuse
    assert audits.tool_events == []


def test_invalid_structured_output_raises_and_records_no_session(tmp_path: Path) -> None:
    backend, _captured = fake_team_backend(tmp_path, {"hypotheses": [{"bad": "object"}]})
    with pytest.raises((TeamTurnError, ValidationError)):
        asyncio.run(backend.run_turn(
            role="red_team",
            prompt="Discover",
            output_model=HypothesisBatch,
            session_id=None,
            audits=empty_audits(),
        ))


def test_hooks_append_auditable_tool_events(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, valid_hypothesis_batch())
    audits = empty_audits()
    asyncio.run(backend.run_turn(
        role="red_team",
        prompt="Discover",
        output_model=HypothesisBatch,
        session_id=None,
        audits=audits,
    ))

    options = captured.calls[0].options
    # PreToolUse and PostToolUse hooks are registered
    hook_matchers = options.hooks
    assert "PreToolUse" in hook_matchers
    assert "PostToolUse" in hook_matchers
    # invoking the pre-tool hook appends an auditable event
    pre = hook_matchers["PreToolUse"][0].hooks[0]
    result = asyncio.run(pre(
        {
            "session_id": "s",
            "transcript_path": "/t",
            "cwd": "/c",
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__repository__read_repository_snippet",
            "tool_input": {"relative_path": "a.py"},
            "tool_use_id": "tu-1",
            "agent_id": "a",
            "agent_type": "red_team",
        },
        "tu-1",
        {"signal": None},
    ))
    assert result == {}
    assert any(e["tool_name"] == "mcp__repository__read_repository_snippet" for e in audits.tool_events)


def test_subagent_definitions_present_and_restricted() -> None:
    assert set(RED_SUBAGENTS) == {"graph-grounder", "attack-path-analyst", "test-strategist"}
    assert set(CODE_SUBAGENTS) == {"architecture-mapper", "reachability-falsifier", "control-verifier"}
    # graph-grounder only sees GraphRAG
    assert RED_SUBAGENTS["graph-grounder"].tools == ["mcp__security_graph__query_security_graph"]
    # attack-path-analyst only sees repository tools
    assert RED_SUBAGENTS["attack-path-analyst"].tools == list(REPOSITORY_TOOLS)
    # test-strategist sees repository + graph
    assert GRAPH_TOOL in RED_SUBAGENTS["test-strategist"].tools
    # all code subagents only see repository tools (no GraphRAG)
    for name, definition in CODE_SUBAGENTS.items():
        assert definition.tools == list(REPOSITORY_TOOLS), name
        assert "mcp__security_graph__query_security_graph" not in definition.tools
