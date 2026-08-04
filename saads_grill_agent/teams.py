"""Persistent adversarial review teams via the Claude Agent SDK.

Three restricted roles — red_team, code_team and judge — are run as isolated,
structured-output Claude Agent SDK sessions. Each role gets only the read-only
repository and security-graph MCP tools it is permitted to use; only the two
team roles may invoke programmatic subagents; the judge is a single session
with both evidence families but no ``Agent`` tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping, TypeVar

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    HookContext,
    HookMatcher,
    ResultMessage,
    query,
)
from pydantic import BaseModel, ValidationError

from saads_attack_agent.agent import _deepseek_environment
from saads_grill_agent.contracts import (
    Adjudication,
    DefenderRebuttal,
    RedResponse,
    VulnerabilityHypothesis,
)

OutputModel = TypeVar("OutputModel", bound=BaseModel)

Role = str  # "red_team" | "code_team" | "judge"

# Per-turn SDK budgets. Plan defaults were 1.50/0.75; live DeepSeek profiling
# with subagents + MCP routinely exceeds that before structured output lands.
TEAM_BUDGET_USD = 5.00
JUDGE_BUDGET_USD = 2.00
# Team turns (profiling/discovery/debate) need headroom for subagents + MCP tools.
TEAM_MAX_TURNS = 40
JUDGE_MAX_TURNS = 12

REPOSITORY_TOOLS = [
    "mcp__repository__list_repository",
    "mcp__repository__search_repository",
    "mcp__repository__read_repository_snippet",
]
GRAPH_TOOL = "mcp__security_graph__query_security_graph"

# Programmatic subagents (verbatim from the plan).
RED_GRAPH_PROMPT = (
    "Ground one LLM attack mechanism and its known controls in the security "
    "graph. Return only structured evidence-backed findings."
)
ATTACK_PATH_PROMPT = (
    "Trace one proposed source-to-sink attack path through repository evidence "
    "using the read-only repository tools. Return only the traced path and the "
    "evidence IDs that support or block it."
)
TEST_STRATEGIST_PROMPT = (
    "Design a non-executing, repository-native regression test for a confirmed "
    "finding using read-only repository and security-graph evidence."
)
ARCHITECTURE_PROMPT = (
    "Map model, agent, RAG, tool, frontend and backend trust seams from "
    "repository evidence using the read-only repository tools."
)
REACHABILITY_PROMPT = (
    "Attempt to prove a proposed attack path unreachable using repository "
    "evidence. Cite the evidence IDs that establish reachability or its absence."
)
CONTROL_PROMPT = (
    "Search for concrete validation, authorization, isolation and approval "
    "controls in repository evidence. Cite the evidence IDs for each control."
)

RED_SUBAGENTS = {
    "graph-grounder": AgentDefinition(
        description="Grounds one LLM attack mechanism and known controls in GraphRAG.",
        prompt=RED_GRAPH_PROMPT,
        tools=["mcp__security_graph__query_security_graph"],
        permissionMode="dontAsk",
    ),
    "attack-path-analyst": AgentDefinition(
        description="Traces one proposed source-to-sink attack path in repository evidence.",
        prompt=ATTACK_PATH_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
    "test-strategist": AgentDefinition(
        description="Designs a non-executing repository-native regression test for a confirmed finding.",
        prompt=TEST_STRATEGIST_PROMPT,
        tools=REPOSITORY_TOOLS + [GRAPH_TOOL],
        permissionMode="dontAsk",
    ),
}

CODE_SUBAGENTS = {
    "architecture-mapper": AgentDefinition(
        description="Maps model, agent, RAG, tool, frontend and backend trust seams from code evidence.",
        prompt=ARCHITECTURE_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
    "reachability-falsifier": AgentDefinition(
        description="Attempts to prove a proposed attack path unreachable using code evidence.",
        prompt=REACHABILITY_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
    "control-verifier": AgentDefinition(
        description="Searches for concrete validation, authorization, isolation and approval controls.",
        prompt=CONTROL_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
}


# Structured-output models for the structured single-turn calls.
class HypothesisBatch(BaseModel):
    hypotheses: list[VulnerabilityHypothesis]


class RebuttalBatch(BaseModel):
    rebuttals: list[DefenderRebuttal]


class RedResponseBatch(BaseModel):
    responses: list[RedResponse]


# Re-export the adjudication contract for judge turns.
AdjudicationVerdict = Adjudication


class TeamTurnError(RuntimeError):
    """A team turn failed; previous state is left unchanged."""


@dataclass
class TeamTurnAudits:
    tool_events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TeamTurnResult:
    output: Any
    session_id: str
    total_cost_usd: float | None
    usage: Any


def _role_tools(role: Role) -> list[str]:
    if role == "red_team":
        return ["Agent"] + REPOSITORY_TOOLS + [GRAPH_TOOL]
    if role == "code_team":
        return ["Agent"] + REPOSITORY_TOOLS
    if role == "judge":
        return REPOSITORY_TOOLS + [GRAPH_TOOL]
    raise TeamTurnError(f"unknown team role: {role}")


def _role_agents(role: Role) -> dict[str, AgentDefinition]:
    if role == "red_team":
        return dict(RED_SUBAGENTS)
    if role == "code_team":
        return dict(CODE_SUBAGENTS)
    return {}


def _role_budget(role: Role) -> float:
    return JUDGE_BUDGET_USD if role == "judge" else TEAM_BUDGET_USD


def _sdk_output_schema(output_model: type[BaseModel]) -> dict[str, Any]:
    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: normalize(item)
                for key, item in value.items()
                if key != "discriminator"
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    return normalize(output_model.model_json_schema())


class TeamBackend:
    """Run one restricted, structured team turn over persistent sessions."""

    def __init__(
        self,
        *,
        target_repo: Any,
        environment: Mapping[str, str] | None = None,
        sdk_query: Callable[..., Any] = query,
        mcp_servers: dict[str, Any] | None = None,
    ) -> None:
        from pathlib import Path
        self._target_repo = Path(target_repo).resolve()
        self._environment = environment
        self._sdk_query = sdk_query
        self._mcp_servers = dict(mcp_servers) if mcp_servers is not None else {}

    async def run_turn(
        self,
        *,
        role: Role,
        prompt: str,
        output_model: type[OutputModel],
        session_id: str | None,
        audits: TeamTurnAudits,
        max_turns: int | None = None,
        enable_subagents: bool = True,
    ) -> TeamTurnResult:
        last_error: Exception | None = None
        for attempt in range(3):
            options = self._build_options(
                role,
                output_model,
                session_id,
                audits,
                max_turns=max_turns,
                # Retries drop subagents — they often burn the turn without
                # returning parent structured output.
                enable_subagents=enable_subagents and attempt == 0,
            )
            structured_output: Any = None
            result_session_id = session_id or ""
            total_cost_usd: float | None = None
            usage: Any = None
            try:
                async for message in self._sdk_query(prompt=prompt, options=options):
                    if not isinstance(message, ResultMessage):
                        continue
                    result_session_id = message.session_id or result_session_id
                    if message.subtype != "success" or message.is_error:
                        raise TeamTurnError(f"team turn failed: {message.subtype}")
                    structured_output = message.structured_output
                    total_cost_usd = getattr(message, "total_cost_usd", None)
                    usage = getattr(message, "usage", None)
            except TeamTurnError as exc:
                # Do not retry hard SDK stop conditions — they usually leave
                # the async transport in a bad state on subsequent attempts.
                raise
            except Exception as exc:  # noqa: BLE001 - normalize SDK errors
                raise TeamTurnError("team turn execution failed") from exc

            if structured_output is None:
                last_error = TeamTurnError("team turn returned no structured output")
                if attempt < 2:
                    continue
                raise last_error
            try:
                validated = output_model.model_validate(structured_output)
            except ValidationError as exc:
                last_error = TeamTurnError(
                    "team turn structured output failed local validation"
                )
                last_error.__cause__ = exc
                if attempt < 2:
                    continue
                raise last_error from exc
            return TeamTurnResult(
                output=validated,
                session_id=result_session_id,
                total_cost_usd=total_cost_usd,
                usage=usage,
            )
        assert last_error is not None
        raise last_error

    def _build_options(
        self,
        role: Role,
        output_model: type[BaseModel],
        session_id: str | None,
        audits: TeamTurnAudits,
        max_turns: int | None = None,
        enable_subagents: bool = True,
    ) -> ClaudeAgentOptions:
        try:
            sdk_env = _deepseek_environment(self._environment or _default_env())
        except Exception:
            sdk_env = {}
        if max_turns is None:
            max_turns = JUDGE_MAX_TURNS if role == "judge" else TEAM_MAX_TURNS
        use_subagents = enable_subagents and role in {"red_team", "code_team"}
        allowed = _role_tools(role)
        if not use_subagents:
            allowed = [tool for tool in allowed if tool != "Agent"]
        return ClaudeAgentOptions(
            cwd=str(self._target_repo),
            setting_sources=[],
            tools=["Agent"] if use_subagents else [],
            allowed_tools=allowed,
            agents=_role_agents(role) if use_subagents else {},
            mcp_servers=self._mcp_servers,
            strict_mcp_config=True,
            permission_mode="dontAsk",
            env=sdk_env,
            output_format={
                "type": "json_schema",
                "schema": _sdk_output_schema(output_model),
            },
            max_turns=max_turns,
            max_budget_usd=_role_budget(role),
            resume=session_id,
            hooks=self._hooks(audits),
        )

    def _hooks(self, audits: TeamTurnAudits) -> dict[str, list[HookMatcher]]:
        async def pre_tool(
            hook_input: Any, tool_use_id: Any, context: HookContext
        ) -> dict[str, Any]:
            audits.tool_events.append(
                {
                    "event": "PreToolUse",
                    "tool_name": hook_input.get("tool_name") if isinstance(hook_input, dict) else getattr(hook_input, "tool_name", None),
                    "tool_input": hook_input.get("tool_input") if isinstance(hook_input, dict) else getattr(hook_input, "tool_input", None),
                }
            )
            return {}

        async def post_tool(
            hook_input: Any, tool_use_id: Any, context: HookContext
        ) -> dict[str, Any]:
            audits.tool_events.append(
                {
                    "event": "PostToolUse",
                    "tool_name": hook_input.get("tool_name") if isinstance(hook_input, dict) else getattr(hook_input, "tool_name", None),
                }
            )
            return {}

        return {
            "PreToolUse": [HookMatcher(matcher=None, hooks=[pre_tool])],
            "PostToolUse": [HookMatcher(matcher=None, hooks=[post_tool])],
        }


def _default_env() -> Mapping[str, str]:
    import os
    return os.environ
