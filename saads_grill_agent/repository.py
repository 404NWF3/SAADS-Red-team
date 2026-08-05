"""Read-only repository snapshot, retrieval and evidence signing.

The target repository is always treated as read-only untrusted data. This
module never executes target code; it only reads validated text files and
signs excerpts as citable :class:`CodeEvidence`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool
from mcp.types import ToolAnnotations

from saads_grill_agent.contracts import CodeEvidence

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_MATCHES = 200
IGNORED_DIRS = frozenset({".git", ".venv", "node_modules", "dist", "build"})
REDACTION = "***REDACTED***"

_LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".md": "markdown",
    ".toml": "toml",
}
_TEST_MANIFEST_NAMES = ("pyproject.toml", "package.json")
_SECRET_NAME = re.compile(
    r"api[_-]?key|secret|token|password|access[_-]?key", re.IGNORECASE
)


class RepositoryAccessError(RuntimeError):
    """A repository path is outside the snapshot, not readable text, or not citable."""


@dataclass(frozen=True)
class RepositoryInventory:
    snapshot_id: str
    git_head: str | None
    file_count: int
    language_counts: dict[str, int]
    test_manifests: list[str]
    manifest_digest: str


@dataclass(frozen=True)
class SearchMatch:
    relative_path: str
    line_number: int
    preview: str


@dataclass(frozen=True)
class SearchResult:
    matches: list[SearchMatch]
    truncated: bool


def _redact(text: str) -> str:
    """Redact values of common secret-looking assignments."""

    def replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}{REDACTION}{match.group(4)}"

    return re.sub(
        r'(?m)^(\s*\w*(?:api[_-]?key|secret|token|password|access[_-]?key)\w*\s*='
        r'\s*)(["\'])([^\n]*?)\2(\s*)$',
        replace,
        text,
        flags=re.IGNORECASE,
    )


class RepositoryEvidenceStore:
    """Resolved, read-only view over one local repository snapshot."""

    def __init__(self, *, root: Path, snapshot_id: str, files: list[str]) -> None:
        self._root = root
        self.snapshot_id = snapshot_id
        self._files = files  # sorted relative POSIX paths of citable text files

    @classmethod
    def open(cls, root: Path) -> RepositoryEvidenceStore:
        resolved_root = Path(root).resolve()
        if not resolved_root.is_dir():
            raise RepositoryAccessError("Repository root is not a directory")
        files = sorted(cls._index_files(resolved_root))
        manifest_digest = sha256(
            "\n".join(files).encode("utf-8")
        ).hexdigest()
        git_head = cls._read_git_head(resolved_root)
        snapshot_id = "snap-" + sha256(
            f"{git_head or ''}\0{manifest_digest}".encode("utf-8")
        ).hexdigest()[:16]
        return cls(root=resolved_root, snapshot_id=snapshot_id, files=files)

    @staticmethod
    def _index_files(root: Path) -> list[str]:
        citable: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if any(part in IGNORED_DIRS for part in relative.parts):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > MAX_FILE_BYTES:
                continue
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            if b"\x00" in raw:
                continue
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            citable.append(relative.as_posix())
        return citable

    @staticmethod
    def _read_git_head(root: Path) -> str | None:
        head_file = root / ".git" / "HEAD"
        if not head_file.is_file():
            return None
        try:
            head = head_file.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if head.startswith("ref:"):
            ref = head[4:].strip()
            ref_file = root / ".git" / ref.replace("/", "\\")
            if not ref_file.is_file():
                # try POSIX join (paths may already use /)
                ref_file = root / ".git" / ref
            if ref_file.is_file():
                try:
                    return ref_file.read_text(encoding="utf-8").strip() or None
                except OSError:
                    return None
            return None
        return head or None

    def _resolve(self, relative_path: str) -> Path:
        if not relative_path:
            raise RepositoryAccessError("path cannot be empty")
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise RepositoryAccessError("absolute paths are not allowed")
        resolved = (self._root / relative_path).resolve()
        if not resolved.is_relative_to(self._root):
            raise RepositoryAccessError("path escapes the repository root")
        if resolved.is_symlink():
            raise RepositoryAccessError("symbolic links are not citable")
        relative_posix = resolved.relative_to(self._root).as_posix()
        if relative_posix not in self._files:
            raise RepositoryAccessError(
                "file is not a citable repository text file"
            )
        return resolved

    def inventory(self) -> RepositoryInventory:
        language_counts: dict[str, int] = {}
        manifests: list[str] = []
        for relative in self._files:
            language = _LANGUAGE_BY_SUFFIX.get(Path(relative).suffix.lower())
            if language is not None:
                language_counts[language] = language_counts.get(language, 0) + 1
            if Path(relative).name in _TEST_MANIFEST_NAMES:
                manifests.append(relative)
        manifest_digest = sha256(
            "\n".join(self._files).encode("utf-8")
        ).hexdigest()
        return RepositoryInventory(
            snapshot_id=self.snapshot_id,
            git_head=self._read_git_head(self._root),
            file_count=len(self._files),
            language_counts=language_counts,
            test_manifests=manifests,
            manifest_digest=manifest_digest,
        )

    def infer_test_frameworks(self) -> list[str]:
        """Detect likely unit-test frameworks from manifests and languages."""
        inventory = self.inventory()
        frameworks: list[str] = []
        for relative in inventory.test_manifests:
            name = Path(relative).name.lower()
            if name == "pyproject.toml" and "pytest" not in frameworks:
                frameworks.append("pytest")
            if name == "package.json":
                try:
                    text = (self._root / relative).read_text(encoding="utf-8")
                except OSError:
                    text = ""
                lowered = text.lower()
                if "vitest" in lowered and "vitest" not in frameworks:
                    frameworks.append("vitest")
                if "jest" in lowered and "jest" not in frameworks:
                    frameworks.append("jest")
                if (
                    "vitest" not in frameworks
                    and "jest" not in frameworks
                    and "javascript" in inventory.language_counts
                ):
                    frameworks.append("vitest")
        if not frameworks and inventory.language_counts.get("python", 0) > 0:
            frameworks.append("pytest")
        return frameworks

    def search(self, query: str, regex: bool = False) -> SearchResult:
        if not query:
            raise RepositoryAccessError("search query cannot be empty")
        matcher: Callable[[str], re.Match[str] | None]
        if regex:
            try:
                pattern = re.compile(query)
            except re.error as exc:
                raise RepositoryAccessError("invalid regular expression") from exc
            matcher = pattern.search
        else:
            needle = query
            matcher = lambda line: line if needle in line else None  # noqa: E731

        matches: list[SearchMatch] = []
        truncated = False
        for relative in self._files:
            if len(matches) >= MAX_SEARCH_MATCHES:
                truncated = True
                break
            path = self._root / relative
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if len(matches) >= MAX_SEARCH_MATCHES:
                    truncated = True
                    break
                if matcher(line) is not None:
                    matches.append(
                        SearchMatch(
                            relative_path=relative,
                            line_number=number,
                            preview=line,
                        )
                    )
        return SearchResult(matches=matches, truncated=truncated)

    def read_snippet(
        self, relative_path: str, line_start: int, line_end: int, claim: str
    ) -> CodeEvidence:
        path = self._resolve(relative_path)
        if line_start < 1:
            raise RepositoryAccessError("line_start must be >= 1")
        if line_end < line_start:
            raise RepositoryAccessError("line_end must be >= line_start")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RepositoryAccessError("file is not readable UTF-8 text") from exc
        lines = text.split("\n")
        if line_end > len(lines):
            raise RepositoryAccessError("line range exceeds file length")
        raw_excerpt = "\n".join(lines[line_start - 1 : line_end])
        raw_sha256 = sha256(raw_excerpt.encode("utf-8")).hexdigest()
        relative_posix = path.relative_to(self._root).as_posix()
        digest_input = (
            f"{self.snapshot_id}\0{relative_posix}\0{line_start}"
            f"\0{line_end}\0{raw_sha256}"
        )
        evidence_id = "code-" + sha256(digest_input.encode("utf-8")).hexdigest()[:16]
        return CodeEvidence(
            evidence_id=evidence_id,
            relative_path=relative_posix,
            line_start=line_start,
            line_end=line_end,
            content_sha256=raw_sha256,
            excerpt=_redact(raw_excerpt),
            claim=claim,
        )


def create_repository_server(
    store: RepositoryEvidenceStore, audit: list[CodeEvidence]
) -> dict[str, Any]:
    """Create a read-only in-process MCP server over the repository evidence."""

    list_schema = {"type": "object", "properties": {}, "additionalProperties": False}
    search_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 1},
            "regex": {"type": "boolean", "default": False},
        },
        "required": ["query"],
        "additionalProperties": False,
    }
    snippet_schema = {
        "type": "object",
        "properties": {
            "relative_path": {"type": "string", "minLength": 1},
            "line_start": {"type": "integer", "minimum": 1},
            "line_end": {"type": "integer", "minimum": 1},
            "claim": {"type": "string", "minLength": 1},
        },
        "required": ["relative_path", "line_start", "line_end", "claim"],
        "additionalProperties": False,
    }

    def _error(message: str) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": message}], "is_error": True}

    @tool(
        "list_repository",
        "List the repository snapshot inventory (languages, test manifests).",
        list_schema,
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False,
            idempotentHint=True, openWorldHint=False,
        ),
    )
    async def list_repository(args: dict[str, Any]) -> dict[str, Any]:
        try:
            inventory = store.inventory()
        except RepositoryAccessError:
            return _error("The repository inventory could not be produced.")
        from dataclasses import asdict
        payload = asdict(inventory)
        return {
            "content": [{"type": "text", "text": str(payload["file_count"])}],
            "structuredContent": payload,
        }

    @tool(
        "search_repository",
        "Search repository text files (literal or regex) for a pattern.",
        search_schema,
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False,
            idempotentHint=True, openWorldHint=False,
        ),
    )
    async def search_repository(args: dict[str, Any]) -> dict[str, Any]:
        try:
            result = store.search(args["query"], regex=bool(args.get("regex", False)))
        except (RepositoryAccessError, KeyError, TypeError):
            return _error("The repository search could not be completed.")
        from dataclasses import asdict
        payload = asdict(result)
        return {
            "content": [{"type": "text", "text": str(len(result.matches))}],
            "structuredContent": payload,
        }

    @tool(
        "read_repository_snippet",
        "Read and sign exact lines of a repository file as citable evidence.",
        snippet_schema,
        annotations=ToolAnnotations(
            readOnlyHint=True, destructiveHint=False,
            idempotentHint=True, openWorldHint=False,
        ),
    )
    async def read_repository_snippet(args: dict[str, Any]) -> dict[str, Any]:
        try:
            evidence = store.read_snippet(
                args["relative_path"],
                int(args["line_start"]),
                int(args["line_end"]),
                args["claim"],
            )
        except (RepositoryAccessError, KeyError, TypeError, ValueError):
            return _error("The repository snippet could not be read.")
        audit.append(evidence)
        return {
            "content": [{"type": "text", "text": evidence.excerpt}],
            "structuredContent": evidence.model_dump(mode="json"),
        }

    return create_sdk_mcp_server(
        name="repository",
        version="1.0.0",
        tools=[list_repository, search_repository, read_repository_snippet],
    )
