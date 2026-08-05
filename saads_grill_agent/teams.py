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
    SdkLimits,
    VulnerabilityHypothesis,
)

OutputModel = TypeVar("OutputModel", bound=BaseModel)

Role = str  # "red_team" | "code_team" | "judge"

# Module aliases of SdkLimits defaults (max_turns None = unlimited).
_DEFAULT_SDK = SdkLimits()
TEAM_BUDGET_USD = _DEFAULT_SDK.team_budget_usd
JUDGE_BUDGET_USD = _DEFAULT_SDK.judge_budget_usd
TEAM_MAX_TURNS = _DEFAULT_SDK.team_max_turns
DISCOVERY_MAX_TURNS = _DEFAULT_SDK.discovery_max_turns
DEBATE_MAX_TURNS = _DEFAULT_SDK.debate_max_turns
JUDGE_MAX_TURNS = _DEFAULT_SDK.judge_max_turns

_MAX_TURNS_UNSET = object()

REPOSITORY_TOOLS = [
    "mcp__repository__list_repository",
    "mcp__repository__search_repository",
    "mcp__repository__read_repository_snippet",
]
GRAPH_TOOL = "mcp__security_graph__query_security_graph"

# Programmatic subagents (verbatim from the plan).
RED_GRAPH_PROMPT = (
    "Ground one LLM attack mechanism and its known controls in the security "
    "graph. Follow the ground-red-team-evidence Skill purpose norms "
    "(threat_modeling, hypothesis_grounding, adjudication_grounding, "
    "test_grounding). Return only structured evidence-backed findings."
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


def _role_tools(role: Role, *, graph_enabled: bool) -> list[str]:
    if role == "red_team":
        tools = ["Agent"] + list(REPOSITORY_TOOLS)
        if graph_enabled:
            tools.extend(["Skill", GRAPH_TOOL])
        return tools
    if role == "code_team":
        return ["Agent"] + list(REPOSITORY_TOOLS)
    if role == "judge":
        tools = list(REPOSITORY_TOOLS)
        if graph_enabled:
            tools.extend(["Skill", GRAPH_TOOL])
        return tools
    raise TeamTurnError(f"unknown team role: {role}")


def _role_agents(role: Role, *, graph_enabled: bool) -> dict[str, AgentDefinition]:
    if role == "red_team":
        agents = dict(RED_SUBAGENTS)
        if not graph_enabled:
            agents.pop("graph-grounder", None)
            strategist = agents["test-strategist"]
            agents["test-strategist"] = AgentDefinition(
                description=strategist.description,
                prompt=strategist.prompt,
                tools=list(REPOSITORY_TOOLS),
                permissionMode=strategist.permissionMode,
            )
        return agents
    if role == "code_team":
        return dict(CODE_SUBAGENTS)
    return {}


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
        sdk_limits: SdkLimits | None = None,
        graph_enabled: bool = False,
        project_root: Any | None = None,
    ) -> None:
        from pathlib import Path
        self._target_repo = Path(target_repo).resolve()
        self._environment = environment
        self._sdk_query = sdk_query
        self._mcp_servers = dict(mcp_servers) if mcp_servers is not None else {}
        self._sdk = sdk_limits if sdk_limits is not None else SdkLimits()
        self._graph_enabled = graph_enabled
        self._project_root = Path(project_root).resolve() if project_root is not None else None

    def _role_budget(self, role: Role) -> float | None:
        return (
            self._sdk.judge_budget_usd
            if role == "judge"
            else self._sdk.team_budget_usd
        )

    def _default_max_turns(self, role: Role) -> int | None:
        return (
            self._sdk.judge_max_turns
            if role == "judge"
            else self._sdk.team_max_turns
        )

    async def run_turn(
        self,
        *,
        role: Role,
        prompt: str,
        output_model: type[OutputModel],
        session_id: str | None,
        audits: TeamTurnAudits,
        max_turns: int | None | object = _MAX_TURNS_UNSET,
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
        max_turns: int | None | object = _MAX_TURNS_UNSET,
        enable_subagents: bool = True,
    ) -> ClaudeAgentOptions:
        try:
            sdk_env = _deepseek_environment(self._environment or _default_env())
        except Exception:
            sdk_env = {}
        resolved_turns = (
            self._default_max_turns(role)
            if max_turns is _MAX_TURNS_UNSET
            else max_turns
        )
        use_subagents = enable_subagents and role in {"red_team", "code_team"}
        graph_role = self._graph_enabled and role in {"red_team", "judge"}
        allowed = _role_tools(role, graph_enabled=self._graph_enabled)
        if not use_subagents:
            allowed = [tool for tool in allowed if tool != "Agent"]
        cwd = (
            str(self._project_root)
            if self._project_root is not None
            else str(self._target_repo)
        )
        tools: list[str] = []
        if use_subagents:
            tools.append("Agent")
        if graph_role:
            tools.append("Skill")
        return ClaudeAgentOptions(
            cwd=cwd,
            setting_sources=["project"] if graph_role else [],
            skills=["ground-red-team-evidence"] if graph_role else [],
            tools=tools,
            allowed_tools=allowed,
            agents=_role_agents(role, graph_enabled=self._graph_enabled)
            if use_subagents
            else {},
            mcp_servers=self._mcp_servers,
            strict_mcp_config=True,
            permission_mode="dontAsk",
            env=sdk_env,
            output_format={
                "type": "json_schema",
                "schema": _sdk_output_schema(output_model),
            },
            max_turns=resolved_turns,
            max_budget_usd=self._role_budget(role),
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
