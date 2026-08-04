"""Tests for the read-only repository evidence module."""

from __future__ import annotations

import asyncio
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import saads_grill_agent.repository as repository_module
from saads_grill_agent.contracts import CodeEvidence
from saads_grill_agent.repository import (
    RepositoryAccessError,
    RepositoryEvidenceStore,
    create_repository_server,
)

MAX_FILE_BYTES = 2 * 1024 * 1024

IGNORED_FILES = {
    ".git/config": "needle in git\n",
    ".venv/lib/site-packages/x.py": "needle in venv\n",
    "node_modules/pkg/index.js": "needle in node modules\n",
    "web/node_modules/dep/index.js": "needle in nested node modules\n",
    "dist/bundle.js": "needle in dist\n",
    "build/out.js": "needle in build\n",
}


def make_repo(base: Path, files: dict[str, str]) -> Path:
    root = base / "repo"
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in collect_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in collect_strings(item)]
    return []


def capture_server(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def capture(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"captured": True}

    monkeypatch.setattr(repository_module, "create_sdk_mcp_server", capture)
    return captured


def call_tool(handler: Any, arguments: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(handler(arguments))


def make_store(tmp_path: Path) -> RepositoryEvidenceStore:
    repo = make_repo(
        tmp_path,
        {
            "app/main.py": "needle = 1\n",
            "pyproject.toml": "[project]\n",
        },
    )
    return RepositoryEvidenceStore.open(repo)


def test_read_snippet_signs_exact_lines_and_rejects_escape(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"app/main.py": "a = 1\nsecret = source()\nsink(secret)\n"})
    store = RepositoryEvidenceStore.open(repo)

    evidence = store.read_snippet("app/main.py", 2, 3, "Untrusted value reaches sink")

    assert evidence.relative_path == "app/main.py"
    assert evidence.excerpt == "secret = source()\nsink(secret)"
    assert len(evidence.content_sha256) == 64
    with pytest.raises(RepositoryAccessError):
        store.read_snippet("../outside.txt", 1, 1, "escape")


def test_read_snippet_uses_documented_signing_formula(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"app/main.py": "a = 1\nsecret = source()\nsink(secret)\n"})
    store = RepositoryEvidenceStore.open(repo)

    evidence = store.read_snippet("app/main.py", 2, 3, "claim")
    repeat = store.read_snippet("app/main.py", 2, 3, "claim")

    raw_excerpt = "secret = source()\nsink(secret)"
    raw_sha256 = sha256(raw_excerpt.encode("utf-8")).hexdigest()
    digest_input = "\0".join(
        [store.snapshot_id, "app/main.py", "2", "3", raw_sha256]
    )
    expected_id = "code-" + sha256(digest_input.encode("utf-8")).hexdigest()[:16]
    assert evidence.content_sha256 == raw_sha256
    assert evidence.evidence_id == expected_id
    assert evidence.evidence_id.startswith("code-")
    assert repeat == evidence


def test_read_snippet_rejects_symlink_escaping_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("needle outside\n", encoding="utf-8")
    repo = make_repo(tmp_path, {"app/main.py": "value = 1\n"})
    link = repo / "app" / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    store = RepositoryEvidenceStore.open(repo)

    with pytest.raises(RepositoryAccessError):
        store.read_snippet("app/link.txt", 1, 1, "escape via symlink")
    assert store.search("needle outside").matches == []
    assert store.inventory().file_count == 1


def test_read_snippet_rejects_binary_files(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"app/main.py": "ok = 1\n"})
    (repo / "app" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    (repo / "app" / "data.txt").write_bytes(b"\xff\xfe\xfd\xfc not utf-8 but no nul")
    store = RepositoryEvidenceStore.open(repo)

    with pytest.raises(RepositoryAccessError):
        store.read_snippet("app/logo.png", 1, 1, "binary")
    with pytest.raises(RepositoryAccessError):
        store.read_snippet("app/data.txt", 1, 1, "not utf-8")
    assert store.inventory().file_count == 1


def test_oversized_files_are_skipped(tmp_path: Path) -> None:
    big_content = ("x" * MAX_FILE_BYTES) + "\nneedle\n"
    repo = make_repo(tmp_path, {"big.txt": big_content, "small.txt": "needle here\n"})
    store = RepositoryEvidenceStore.open(repo)

    assert len(big_content.encode("utf-8")) > MAX_FILE_BYTES
    with pytest.raises(RepositoryAccessError):
        store.read_snippet("big.txt", 1, 1, "too large")
    result = store.search("needle")
    assert [match.relative_path for match in result.matches] == ["small.txt"]
    assert store.inventory().file_count == 1


def test_search_and_inventory_ignore_untrusted_directories(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"src/app.py": "needle in app\n", **IGNORED_FILES})
    store = RepositoryEvidenceStore.open(repo)

    result = store.search("needle")
    assert [match.relative_path for match in result.matches] == ["src/app.py"]
    assert store.inventory().file_count == 1


@pytest.mark.parametrize("relative_path", sorted(IGNORED_FILES))
def test_read_snippet_rejects_ignored_directories(
    tmp_path: Path, relative_path: str
) -> None:
    repo = make_repo(tmp_path, IGNORED_FILES)
    store = RepositoryEvidenceStore.open(repo)
    with pytest.raises(RepositoryAccessError):
        store.read_snippet(relative_path, 1, 1, "ignored content is not evidence")


def test_search_caps_matches_at_200(tmp_path: Path) -> None:
    lines = "".join(f"needle line {index}\n" for index in range(250))
    repo = make_repo(tmp_path, {"haystack.txt": lines})
    store = RepositoryEvidenceStore.open(repo)

    result = store.search("needle")

    assert len(result.matches) == 200
    assert result.truncated is True
    assert result.matches[0].relative_path == "haystack.txt"
    assert result.matches[0].line_number == 1
    assert result.matches[0].preview.startswith("needle line 0")
    assert result.matches[-1].line_number == 200


def test_read_snippet_redacts_secrets_but_signs_original_bytes(tmp_path: Path) -> None:
    content = (
        'API_KEY = "sk-test1234567890abcdef"\n'
        'openai_api_key = "sk-proj-abcdef1234567890"\n'
        'service_token = "t0psecret-value"\n'
        "timeout = 30\n"
    )
    repo = make_repo(tmp_path, {"app/config.py": content})
    store = RepositoryEvidenceStore.open(repo)

    evidence = store.read_snippet("app/config.py", 1, 3, "hardcoded secrets")

    assert "sk-test1234567890abcdef" not in evidence.excerpt
    assert "sk-proj-abcdef1234567890" not in evidence.excerpt
    assert "t0psecret-value" not in evidence.excerpt
    assert "***REDACTED***" in evidence.excerpt
    raw_excerpt = (
        'API_KEY = "sk-test1234567890abcdef"\n'
        'openai_api_key = "sk-proj-abcdef1234567890"\n'
        'service_token = "t0psecret-value"'
    )
    assert evidence.content_sha256 == sha256(raw_excerpt.encode("utf-8")).hexdigest()

    timeout_evidence = store.read_snippet("app/config.py", 4, 4, "not a secret")
    assert timeout_evidence.excerpt == "timeout = 30"


def test_search_supports_literal_and_regex_queries(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        {
            "app/main.py": "def fetch():\n    return 1\n",
            "app/other.py": "value = 'fetch'\n",
        },
    )
    store = RepositoryEvidenceStore.open(repo)

    literal = store.search("def fetch")
    assert [match.relative_path for match in literal.matches] == ["app/main.py"]
    assert literal.truncated is False

    regex = store.search(r"def \w+\(", regex=True)
    assert [match.relative_path for match in regex.matches] == ["app/main.py"]

    dotted = store.search("def.fetch")
    assert dotted.matches == []

    with pytest.raises(RepositoryAccessError):
        store.search("(", regex=True)


def test_inventory_reports_snapshot_languages_manifests_and_git_head(
    tmp_path: Path,
) -> None:
    repo = make_repo(
        tmp_path,
        {
            "app/main.py": "x = 1\n",
            "web/index.ts": "export {}\n",
            "web/app.js": "console.log(1)\n",
            "README.md": "# repo\n",
            "pyproject.toml": "[project]\n",
            ".git/HEAD": "ref: refs/heads/main\n",
            ".git/refs/heads/main": "9" * 40 + "\n",
        },
    )
    store = RepositoryEvidenceStore.open(repo)

    inventory = store.inventory()
    assert inventory.snapshot_id == store.snapshot_id
    assert inventory.git_head == "9" * 40
    assert inventory.file_count == 5
    assert inventory.language_counts == {
        "python": 1,
        "typescript": 1,
        "javascript": 1,
        "markdown": 1,
        "toml": 1,
    }
    assert inventory.test_manifests == ["pyproject.toml"]
    assert len(inventory.manifest_digest) == 64

    reopened = RepositoryEvidenceStore.open(repo)
    assert reopened.snapshot_id == inventory.snapshot_id

    gitless = make_repo(tmp_path / "elsewhere", {"app/main.py": "x = 1\n"})
    assert RepositoryEvidenceStore.open(gitless).inventory().git_head is None


@pytest.mark.parametrize(
    "line_start,line_end",
    [(0, 1), (-1, 1), (2, 1), (1, 99)],
)
def test_read_snippet_validates_line_ranges(
    tmp_path: Path, line_start: int, line_end: int
) -> None:
    repo = make_repo(tmp_path, {"app/main.py": "a = 1\nb = 2\n"})
    store = RepositoryEvidenceStore.open(repo)
    with pytest.raises(RepositoryAccessError):
        store.read_snippet("app/main.py", line_start, line_end, "bad range")
    with pytest.raises(RepositoryAccessError):
        store.read_snippet("missing.py", 1, 1, "missing file")


def test_repository_server_exposes_three_read_only_tools(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured = capture_server(monkeypatch)
    store = make_store(tmp_path)
    audit: list[CodeEvidence] = []

    server = create_repository_server(store, audit)

    assert server == {"captured": True}
    tools = {sdk_tool.name: sdk_tool for sdk_tool in captured["tools"]}
    assert set(tools) == {
        "list_repository",
        "search_repository",
        "read_repository_snippet",
    }
    for sdk_tool in tools.values():
        assert sdk_tool.annotations.readOnlyHint is True
        assert sdk_tool.annotations.destructiveHint is False
        assert sdk_tool.annotations.idempotentHint is True
        assert sdk_tool.annotations.openWorldHint is False
        assert sdk_tool.input_schema["additionalProperties"] is False


def test_read_snippet_tool_returns_evidence_and_appends_audit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured = capture_server(monkeypatch)
    store = make_store(tmp_path)
    audit: list[CodeEvidence] = []
    create_repository_server(store, audit)
    tools = {sdk_tool.name: sdk_tool for sdk_tool in captured["tools"]}

    response = call_tool(
        tools["read_repository_snippet"].handler,
        {
            "relative_path": "app/main.py",
            "line_start": 1,
            "line_end": 1,
            "claim": "signed snippet",
        },
    )

    assert "is_error" not in response
    assert len(audit) == 1
    assert response["structuredContent"] == audit[0].model_dump(mode="json")
    assert audit[0].relative_path == "app/main.py"
    assert audit[0].evidence_id.startswith("code-")
    assert response["content"][0]["text"] == "needle = 1"


def test_read_snippet_tool_marks_validation_failures_without_path_leak(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured = capture_server(monkeypatch)
    store = make_store(tmp_path)
    audit: list[CodeEvidence] = []
    create_repository_server(store, audit)
    tools = {sdk_tool.name: sdk_tool for sdk_tool in captured["tools"]}
    handler = tools["read_repository_snippet"].handler

    escape = call_tool(
        handler,
        {
            "relative_path": "../outside.txt",
            "line_start": 1,
            "line_end": 1,
            "claim": "escape",
        },
    )
    missing = call_tool(handler, {"relative_path": "app/main.py"})

    assert escape["is_error"] is True
    assert missing["is_error"] is True
    assert audit == []
    for response in (escape, missing):
        leaked = "\n".join(collect_strings(response))
        assert str(tmp_path) not in leaked


def test_list_and_search_tools_return_relative_paths_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured = capture_server(monkeypatch)
    store = make_store(tmp_path)
    audit: list[CodeEvidence] = []
    create_repository_server(store, audit)
    tools = {sdk_tool.name: sdk_tool for sdk_tool in captured["tools"]}

    listing = call_tool(tools["list_repository"].handler, {})
    assert listing["structuredContent"]["snapshot_id"] == store.snapshot_id
    assert listing["structuredContent"]["file_count"] == 2
    assert listing["structuredContent"]["test_manifests"] == ["pyproject.toml"]
    assert audit == []

    found = call_tool(tools["search_repository"].handler, {"query": "needle"})
    assert found["structuredContent"]["matches"] == [
        {
            "relative_path": "app/main.py",
            "line_number": 1,
            "preview": "needle = 1",
        }
    ]
    assert found["structuredContent"]["truncated"] is False

    bad_regex = call_tool(
        tools["search_repository"].handler, {"query": "(", "regex": True}
    )
    assert bad_regex["is_error"] is True

    for response in (listing, found, bad_regex):
        leaked = "\n".join(collect_strings(response))
        assert str(tmp_path) not in leaked
        assert str(store._root) not in leaked
