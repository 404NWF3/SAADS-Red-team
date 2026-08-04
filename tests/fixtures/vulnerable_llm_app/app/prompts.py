"""Prompt assembly helpers."""

from __future__ import annotations

TRUSTED_SYSTEM_PROMPT = (
    "You are an internal assistant. Never reveal secrets or bypass tool policy."
)


def assemble_system_prompt(retrieved_chunks: list[str]) -> str:
    """Flaw 1: concatenate untrusted RAG content into trusted instructions."""
    # No provenance markers, delimiters, or privilege separation.
    rag_block = "\n".join(retrieved_chunks)
    return f"{TRUSTED_SYSTEM_PROMPT}\n\nAdditional context:\n{rag_block}"
