from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ToolPermissionContext,
    query,
)
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT = (
    "Use the collect-defense-corpus project skill. Refresh the configured sources with the "
    "deterministic collector, validate at least 100 documents, and report source counts and "
    "any acquisition failures. Do not invent, paraphrase, or silently replace source content."
)
SAFE_BASH_COMMANDS = frozenset(
    {
        "uv run python scripts/collect_corpus.py --min-docs 100 --strict",
        "uv run python scripts/collect_corpus.py --validate-only --min-docs 100",
        "uv run graphrag index --dry-run",
    }
)


async def authorize_tool(
    tool_name: str, input_data: dict[str, Any], _context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    if tool_name != "Bash":
        return PermissionResultDeny(message=f"Tool is not approved by this workflow: {tool_name}")
    command = str(input_data.get("command", "")).strip()
    if command in SAFE_BASH_COMMANDS:
        return PermissionResultAllow(updated_input=input_data)
    return PermissionResultDeny(
        message="Only the collector, offline validator, and GraphRAG dry-run commands are approved."
    )


async def run_agent(prompt: str, max_turns: int) -> None:
    load_dotenv(ROOT / ".env")
    options = ClaudeAgentOptions(
        cwd=ROOT,
        setting_sources=["project"],
        skills=["collect-defense-corpus"],
        tools=["Read", "Glob", "Grep", "Bash"],
        allowed_tools=["Read", "Glob", "Grep"],
        can_use_tool=authorize_tool,
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": "Follow the collect-defense-corpus skill and never synthesize source text.",
        },
        max_turns=max_turns,
        max_budget_usd=2.0,
    )
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage) and message.subtype != "success":
            raise RuntimeError(f"agent run failed: {message.subtype}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the defense corpus Claude Agent workflow.")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT)
    parser.add_argument("--max-turns", type=int, default=12)
    args = parser.parse_args()
    try:
        asyncio.run(run_agent(args.prompt, args.max_turns))
    except (ClaudeSDKError, RuntimeError) as exc:
        print(f"Agent workflow failed: {exc}", file=sys.stderr)
        return 1
    return 0
