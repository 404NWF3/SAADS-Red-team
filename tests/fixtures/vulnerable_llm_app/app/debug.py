"""Debug helpers that intentionally leak prompt material."""

from __future__ import annotations

from app.prompts import assemble_system_prompt
from app.rag import retrieve


def assembled_system_prompt_for_debug(query: str = "status") -> str:
    """Flaw 3: expose the assembled system prompt through a debug path."""
    chunks = retrieve(query)
    return assemble_system_prompt(chunks)
