from __future__ import annotations

import asyncio

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from llm_defense_graphrag.agent import authorize_tool
from llm_defense_graphrag.corpus import html_to_markdown, metadata_markdown, slugify, word_count


def test_html_to_markdown_removes_navigation() -> None:
    title, body = html_to_markdown(
        """
        <html><body><nav>ignore me</nav><article>
        <h1>Prompt Injection</h1><p>Untrusted input can alter model behavior.</p>
        <h2>Mitigation</h2><ul><li>Separate instructions from data.</li></ul>
        </article><footer>ignore me too</footer></body></html>
        """
    )
    assert title == "Prompt Injection"
    assert "## Mitigation" in body
    assert "- Separate instructions from data." in body
    assert "ignore me" not in body


def test_metadata_markdown_has_required_frontmatter() -> None:
    text = metadata_markdown(
        {
            "title": "Example",
            "source": "Owner",
            "canonical_url": "https://example.test/source",
        },
        "# Example\n\nSubstantive source text.",
    )
    assert text.startswith("---\ntitle: Example\n")
    assert "canonical_url: https://example.test/source" in text
    assert text.endswith("Substantive source text.\n")


def test_slug_and_word_count_are_deterministic() -> None:
    assert slugify("AML.T0043.001") == "aml-t0043-001"
    assert word_count("Prompt-injection defense uses two controls.") == 5


def test_agent_only_allows_deterministic_collector_commands() -> None:
    allowed = asyncio.run(
        authorize_tool(
            "Bash",
            {"command": "uv run python scripts/collect_corpus.py --validate-only --min-docs 100"},
            None,  # type: ignore[arg-type]
        )
    )
    denied = asyncio.run(
        authorize_tool("Bash", {"command": "Remove-Item -Recurse input"}, None)  # type: ignore[arg-type]
    )
    assert isinstance(allowed, PermissionResultAllow)
    assert isinstance(denied, PermissionResultDeny)
