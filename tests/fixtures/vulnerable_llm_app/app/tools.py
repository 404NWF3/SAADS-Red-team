"""Tool registry with one late-binding flaw and one defended high-risk tool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class PlannedExecution:
    """Argument planning completed before tool-name authorization."""

    call: ToolCall
    prepared_args: dict[str, Any]
    side_effects_planned: bool


TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], str]] = {}


def register(name: str, handler: Callable[[dict[str, Any]], str]) -> None:
    TOOL_HANDLERS[name] = handler


def plan_tool_execution(call: ToolCall) -> PlannedExecution:
    """Flaw 2: plan/prepare arguments before validating the selected tool name."""
    prepared = dict(call.arguments)
    # Planning mutates and stages side effects using the model-selected name
    # before any allowlist or capability check runs.
    prepared["_staged_for"] = call.name
    return PlannedExecution(
        call=call,
        prepared_args=prepared,
        side_effects_planned=True,
    )


def execute_planned(plan: PlannedExecution) -> str:
    """Authorize the tool name only after argument execution planning."""
    name = plan.call.name
    if name not in TOOL_HANDLERS:
        raise PermissionError(f"unknown tool: {name}")
    return TOOL_HANDLERS[name](plan.prepared_args)


def run_model_selected_tool(call: ToolCall) -> str:
    """Entry point used by the agent loop for model-selected tools."""
    plan = plan_tool_execution(call)
    return execute_planned(plan)


# --- Flaw 4 defended non-finding: high-risk file write with hard controls ---

ALLOWED_WRITE_PATHS = frozenset({"outputs/approved.txt", "outputs/notes.txt"})


def write_file_tool(
    arguments: dict[str, Any],
    *,
    human_approved: bool = False,
) -> str:
    """High-risk file write protected by hard allowlist + human approval."""
    path = str(arguments.get("path", ""))
    content = str(arguments.get("content", ""))
    if path not in ALLOWED_WRITE_PATHS:
        raise PermissionError(f"path not allowlisted: {path}")
    if not human_approved:
        raise PermissionError("human approval required before file write")
    # Fixture does not touch the real filesystem; approval + allowlist is the control.
    return f"approved-write:{path}:{len(content)}"


register("echo", lambda args: str(args.get("text", "")))
register("write_file", lambda args: write_file_tool(args, human_approved=False))
