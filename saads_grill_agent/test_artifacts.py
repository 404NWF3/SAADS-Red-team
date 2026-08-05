"""Validate and publish unexecuted regression-test drafts."""

from __future__ import annotations

import ast
import json
import re
from enum import Enum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, PrivateAttr

from saads_grill_agent.contracts import Finding, GeneratedTestDraft, RepositoryProfile


_MAX_SOURCE_BYTES = 30 * 1024
_SAFE_FINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SEAL = object()
_PYTHON_FORBIDDEN_MODULES = frozenset(
    {"os", "subprocess", "socket", "requests", "urllib", "httpx"}
)
_PYTHON_FORBIDDEN_CALLS = frozenset({"eval", "exec", "os.system"})
_DESTRUCTIVE_METHODS = frozenset({"write_text", "write_bytes", "unlink", "rmdir"})
_WRITE_OPEN_MODES = frozenset({"w", "a", "x", "r+", "w+", "a+", "x+"})
_STDLIB_OR_TOOLING_ROOTS = frozenset({
    "pytest", "unittest", "typing", "collections", "json", "re", "sys",
    "pathlib", "fastapi", "httpx", "starlette", "pydantic", "vitest",
    "jest", "node_modules", "fixtures",
})
_JAVASCRIPT_FORBIDDEN = (
    re.compile(r"""(?:from\s+['"]|require\(\s*['"])(?:child_process|net|dgram)['"]"""),
    re.compile(r"\b(?:child_process|net|dgram)\b"),
    re.compile(r"\bimport\s*\("),
    re.compile(r"\bprocess\s*(?:\.|\[)"),
    re.compile(r"\b(?:exec|execFile|spawn|spawnSync)\s*\("),
    re.compile(r"\b(?:writeFile|appendFile|rm|unlink)\s*\("),
)
_JS_IMPORT = re.compile(
    r"""(?:from\s+['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)|import\s+['"]([^'"]+)['"])"""
)


class TestArtifactPolicyError(ValueError):
    """Raised when a generated test cannot be safely retained as an artifact."""

    __test__ = False


class TestArtifactStatus(str, Enum):
    """Lifecycle status for published (or failed) test artifacts.

    ``generation_failed`` is recorded after two failed regenerations; the
    orchestrator owns retry wiring and does not live in this module.
    """

    __test__ = False

    UNEXECUTED = "unexecuted"
    GENERATION_FAILED = "generation_failed"


class SnapshotObjection(BaseModel):
    """A concrete import/path mismatch against a repository snapshot."""

    model_config = ConfigDict(frozen=True)

    kind: Literal["missing_import", "missing_path", "missing_fixture"]
    reference: str
    message: str


class ValidatedTestArtifact(BaseModel):
    """A reviewed draft that can be persisted without being executed.

    Only :func:`validate_test_draft` may seal instances accepted by writers.
    """

    model_config = ConfigDict(frozen=True)

    test_id: str
    finding_id: str
    snapshot_id: str
    language: str
    framework: str
    suggested_copy_destination: str
    source: str
    suggested_run_command: str
    extension: str
    status: TestArtifactStatus = TestArtifactStatus.UNEXECUTED
    _seal: object = PrivateAttr(default=None)


def validate_test_draft(
    draft: GeneratedTestDraft,
    finding: Finding | None,
    profile: RepositoryProfile,
) -> ValidatedTestArtifact:
    """Fail closed unless a draft is safe and matches a confirmed finding."""
    _validate_finding(draft, finding)
    _validate_metadata(draft, profile)
    if draft.language == "python":
        _validate_python_source(draft.source)
        extension = ".py"
    else:
        _validate_javascript_source(draft.source)
        extension = ".test.ts" if draft.language == "typescript" else ".test.js"

    artifact = ValidatedTestArtifact(
        test_id=draft.test_id,
        finding_id=draft.finding_id,
        snapshot_id=profile.snapshot_id,
        language=draft.language,
        framework=draft.framework,
        suggested_copy_destination=draft.suggested_target_path,
        source=draft.source,
        suggested_run_command=draft.suggested_run_command,
        extension=extension,
        status=TestArtifactStatus.UNEXECUTED,
    )
    object.__setattr__(artifact, "_seal", _SEAL)
    return artifact


def write_test_artifact(
    draft: GeneratedTestDraft,
    finding: Finding | None,
    profile: RepositoryProfile,
    run_dir: Path,
    target_repo: Path,
) -> Path:
    """Re-validate then write an unexecuted draft under ``run_dir/tests`` only."""
    artifact = validate_test_draft(draft, finding, profile)
    if artifact._seal is not _SEAL:
        raise TestArtifactPolicyError("artifact was not produced by validate_test_draft")
    if not _SAFE_FINDING_ID.fullmatch(artifact.finding_id):
        raise TestArtifactPolicyError("finding ID is not safe for an artifact filename")

    tests_dir = (run_dir / "tests").resolve()
    artifact_path = (tests_dir / f"{artifact.finding_id}{artifact.extension}").resolve()
    _assert_outside_target(artifact_path, target_repo)
    try:
        artifact_path.relative_to(tests_dir)
    except ValueError as exc:
        raise TestArtifactPolicyError(
            "test artifacts must resolve under run_dir/tests"
        ) from exc

    tests_dir.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(artifact.source, encoding="utf-8", newline="\n")

    manifest_path = run_dir / "test_manifest.json"
    artifacts = _load_manifest(manifest_path)
    record = {
        "finding_id": artifact.finding_id,
        "framework": artifact.framework,
        "snapshot_id": artifact.snapshot_id,
        "status": artifact.status.value,
        "suggested_copy_destination": artifact.suggested_copy_destination,
        "suggested_run_command": artifact.suggested_run_command,
        "test_id": artifact.test_id,
    }
    artifacts = [
        item for item in artifacts
        if item.get("test_id") != artifact.test_id
    ]
    artifacts.append(record)
    manifest_path.write_text(
        json.dumps({"artifacts": artifacts}, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )
    return artifact_path


def collect_snapshot_objections(
    draft: GeneratedTestDraft,
    repository_relative_paths: set[str] | frozenset[str],
) -> list[SnapshotObjection]:
    """Return structured objections when draft imports/paths are absent.

    Intended for code-team review before regeneration. The orchestrator wires
    up to two regenerations and records :attr:`TestArtifactStatus.GENERATION_FAILED`
    afterward; this helper does not call TeamBackend or agents.
    """
    normalized = {_normalize_repo_path(path) for path in repository_relative_paths}
    top_levels = {path.split("/", 1)[0] for path in normalized if path}
    objections: list[SnapshotObjection] = []

    if draft.language == "python":
        objections.extend(_python_import_objections(draft.source, normalized, top_levels))
    else:
        objections.extend(_javascript_import_objections(draft.source, normalized, top_levels))

    target = _normalize_repo_path(draft.suggested_target_path)
    if target and not _is_absolute_path(draft.suggested_target_path):
        parent = str(PurePosixPath(target).parent)
        if parent not in {".", ""} and not _path_exists_in_snapshot(parent, normalized):
            # Only object when the parent package/dir is claimed by the repo layout.
            root = parent.split("/", 1)[0]
            if root in top_levels:
                objections.append(SnapshotObjection(
                    kind="missing_path",
                    reference=target,
                    message=f"suggested target path parent does not exist: {parent}",
                ))

    for dependency in draft.mocked_dependencies:
        module_path = dependency.replace(".", "/")
        root = module_path.split("/", 1)[0]
        if root in top_levels and not _module_exists(module_path, normalized):
            objections.append(SnapshotObjection(
                kind="missing_import",
                reference=dependency,
                message=f"mocked dependency is not present in the snapshot: {dependency}",
            ))

    for fixture in draft.required_fixtures:
        # Fixtures are names, not paths; only object when a same-named path is expected.
        if "/" in fixture or "\\" in fixture or fixture.endswith((".py", ".ts", ".js")):
            path = _normalize_repo_path(fixture)
            if path and not _path_exists_in_snapshot(path, normalized):
                objections.append(SnapshotObjection(
                    kind="missing_fixture",
                    reference=fixture,
                    message=f"required fixture path is not present in the snapshot: {fixture}",
                ))

    return objections


def _validate_finding(draft: GeneratedTestDraft, finding: Finding | None) -> None:
    if finding is None:
        raise TestArtifactPolicyError("confirmed finding is required")
    status = getattr(finding, "status", "confirmed")
    if status != "confirmed":
        raise TestArtifactPolicyError("finding is not confirmed")
    if draft.finding_id != finding.finding_id:
        raise TestArtifactPolicyError("draft finding ID does not match finding")
    if not finding.code_evidence_ids and not finding.graph_evidence_ids:
        raise TestArtifactPolicyError("finding requires signed evidence IDs")


def _validate_metadata(draft: GeneratedTestDraft, profile: RepositoryProfile) -> None:
    if not draft.finding_id or not _SAFE_FINDING_ID.fullmatch(draft.finding_id):
        raise TestArtifactPolicyError("draft requires a safe finding ID")
    if not profile.profile_evidence_ids:
        raise TestArtifactPolicyError("repository profile requires signed evidence IDs")
    allowed_frameworks = list(profile.test_frameworks)
    if not allowed_frameworks:
        # Live profiles often omit frameworks; fall back to the draft's own
        # language-compatible framework rather than aborting the assessment.
        if draft.framework == "pytest" and draft.language == "python":
            allowed_frameworks = ["pytest"]
        elif draft.framework in {"vitest", "jest"} and draft.language in {
            "typescript",
            "javascript",
        }:
            allowed_frameworks = [draft.framework]
    if draft.framework not in allowed_frameworks:
        raise TestArtifactPolicyError("draft framework is not present in the repository profile")
    if (draft.language == "python") != (draft.framework == "pytest"):
        raise TestArtifactPolicyError("draft language and framework do not match")
    if _is_absolute_path(draft.suggested_target_path):
        raise TestArtifactPolicyError("suggested target path must be relative")
    if len(draft.source.encode("utf-8")) > _MAX_SOURCE_BYTES:
        raise TestArtifactPolicyError("draft source exceeds 30 KiB")


def _validate_python_source(source: str) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise TestArtifactPolicyError("draft source is not valid Python") from exc

    aliases = _collect_python_aliases(tree)
    for bound, target in aliases.items():
        root = target.split(".", 1)[0]
        if root in _PYTHON_FORBIDDEN_MODULES:
            raise TestArtifactPolicyError("Python draft imports a forbidden module")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = _resolve_call_name(node.func, aliases)
            if call_name in _PYTHON_FORBIDDEN_CALLS or call_name in {"eval", "exec"}:
                raise TestArtifactPolicyError("Python draft invokes a forbidden function")
            if call_name == "open" or call_name.endswith(".open"):
                if _open_is_destructive(node):
                    raise TestArtifactPolicyError("Python draft writes to the target repository")
            if isinstance(node.func, ast.Attribute) and node.func.attr in _DESTRUCTIVE_METHODS:
                raise TestArtifactPolicyError("Python draft writes to the target repository")
            if any(call_name.endswith(f".{method}") for method in _DESTRUCTIVE_METHODS):
                raise TestArtifactPolicyError("Python draft writes to the target repository")


def _collect_python_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name
                aliases[bound] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound = alias.asname or alias.name
                aliases[bound] = f"{node.module}.{alias.name}"
    return aliases


def _resolve_call_name(node: ast.expr, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _resolve_call_name(node.value, aliases)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return _resolve_call_name(node.func, aliases)
    return ""


def _open_is_destructive(node: ast.Call) -> bool:
    """Reject write-capable open() calls; fail closed when mode is unclear."""
    mode: str | None = None
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        if isinstance(node.args[1].value, str):
            mode = node.args[1].value
    for keyword in node.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                mode = keyword.value.value
    if mode is None:
        # Single-arg open defaults to read; still reject bare open with extra
        # non-literal args that could enable writing.
        if len(node.args) <= 1 and not any(kw.arg == "mode" for kw in node.keywords):
            return False
        return True
    base = mode.replace("b", "").replace("t", "").replace("U", "")
    return base in _WRITE_OPEN_MODES or any(flag in mode for flag in "wax+")


def _validate_javascript_source(source: str) -> None:
    for forbidden in _JAVASCRIPT_FORBIDDEN:
        if forbidden.search(source):
            raise TestArtifactPolicyError("JavaScript draft uses a forbidden capability")
    if re.search(r"\bfetch\s*\(", source) and not _has_mocked_fetch(source):
        raise TestArtifactPolicyError("JavaScript draft uses unmocked fetch")
    if re.search(r"\baxios\b", source) and not _has_mocked_axios(source):
        raise TestArtifactPolicyError("JavaScript draft uses unmocked axios")


def _has_mocked_fetch(source: str) -> bool:
    return bool(re.search(
        r"""(?:vi\.stubGlobal\(\s*['"]fetch['"]|global\.fetch\s*=|jest\.spyOn\(\s*global(?:This)?\s*,\s*['"]fetch['"])""",
        source,
    ))


def _has_mocked_axios(source: str) -> bool:
    return bool(re.search(r"""(?:vi|jest)\.mock\(\s*['"]axios['"]""", source))


def _assert_outside_target(path: Path, target_repo: Path) -> None:
    target_root = target_repo.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(target_root)
    except ValueError:
        return
    raise TestArtifactPolicyError(
        "refusing to write test artifact inside the target repository"
    )


def _is_absolute_path(path: str) -> bool:
    return path.startswith(("/", "\\")) or Path(path).is_absolute() or PureWindowsPath(path).is_absolute()


def _normalize_repo_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _path_exists_in_snapshot(path: str, normalized: set[str]) -> bool:
    path = _normalize_repo_path(path)
    if path in normalized:
        return True
    prefix = path.rstrip("/") + "/"
    return any(item.startswith(prefix) for item in normalized)


def _module_exists(module_path: str, normalized: set[str]) -> bool:
    candidates = (
        module_path,
        f"{module_path}.py",
        f"{module_path}.ts",
        f"{module_path}.js",
        f"{module_path}.tsx",
        f"{module_path}.jsx",
        f"{module_path}/__init__.py",
        f"{module_path}/index.ts",
        f"{module_path}/index.js",
    )
    return any(_path_exists_in_snapshot(candidate, normalized) for candidate in candidates)


def _python_import_objections(
    source: str,
    normalized: set[str],
    top_levels: set[str],
) -> list[SnapshotObjection]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    objections: list[SnapshotObjection] = []
    seen: set[str] = set()
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.append(node.module)
        for module in modules:
            root = module.split(".", 1)[0]
            if root in _STDLIB_OR_TOOLING_ROOTS or root in _PYTHON_FORBIDDEN_MODULES:
                continue
            if root not in top_levels:
                continue
            module_path = module.replace(".", "/")
            if module_path in seen:
                continue
            seen.add(module_path)
            if not _module_exists(module_path, normalized):
                objections.append(SnapshotObjection(
                    kind="missing_import",
                    reference=module,
                    message=f"import is not present in the snapshot: {module}",
                ))
    return objections


def _javascript_import_objections(
    source: str,
    normalized: set[str],
    top_levels: set[str],
) -> list[SnapshotObjection]:
    objections: list[SnapshotObjection] = []
    seen: set[str] = set()
    for match in _JS_IMPORT.finditer(source):
        spec = next(group for group in match.groups() if group)
        if not spec.startswith(".") and not spec.startswith("/"):
            root = spec.split("/", 1)[0]
            if root in _STDLIB_OR_TOOLING_ROOTS or root.startswith("@"):
                continue
            if root not in top_levels:
                continue
            module_path = spec
        else:
            module_path = _normalize_repo_path(spec)
            root = module_path.split("/", 1)[0]
            if root not in top_levels and not spec.startswith("."):
                continue
        if module_path in seen:
            continue
        seen.add(module_path)
        # Relative imports need the caller path to resolve; only check bare package paths.
        if spec.startswith("."):
            continue
        if not _module_exists(module_path, normalized):
            objections.append(SnapshotObjection(
                kind="missing_import",
                reference=spec,
                message=f"import is not present in the snapshot: {spec}",
            ))
    return objections


def _load_manifest(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TestArtifactPolicyError("existing test manifest is invalid") from exc
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
    if not isinstance(artifacts, list) or not all(isinstance(item, dict) for item in artifacts):
        raise TestArtifactPolicyError("existing test manifest is invalid")
    return artifacts
