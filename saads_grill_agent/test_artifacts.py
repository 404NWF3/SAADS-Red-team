"""Validate and publish unexecuted regression-test drafts."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path, PureWindowsPath

from pydantic import BaseModel, ConfigDict

from saads_grill_agent.contracts import GeneratedTestDraft, RepositoryProfile


_MAX_SOURCE_BYTES = 30 * 1024
_SAFE_FINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PYTHON_FORBIDDEN_MODULES = frozenset(
    {"subprocess", "socket", "requests", "urllib", "httpx"}
)
_PYTHON_FORBIDDEN_CALLS = frozenset({"eval", "exec", "os.system"})
_JAVASCRIPT_FORBIDDEN = (
    re.compile(r"""(?:from\s+['"]|require\(\s*['"])(?:child_process|net|dgram)['"]"""),
    re.compile(r"\b(?:child_process|net|dgram)\b"),
    re.compile(r"\bimport\s*\("),
    re.compile(r"\bprocess\s*(?:\.|\[)"),
    re.compile(r"\b(?:exec|execFile|spawn|spawnSync)\s*\("),
    re.compile(r"\b(?:writeFile|appendFile|rm|unlink)\s*\("),
)


class TestArtifactPolicyError(ValueError):
    """Raised when a generated test cannot be safely retained as an artifact."""

    __test__ = False


class ValidatedTestArtifact(BaseModel):
    """A reviewed draft that can be persisted without being executed."""

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


def validate_test_draft(
    draft: GeneratedTestDraft,
    profile: RepositoryProfile,
) -> ValidatedTestArtifact:
    """Fail closed unless a draft is safe and matches the profiled test stack."""
    _validate_metadata(draft, profile)
    if draft.language == "python":
        _validate_python_source(draft.source)
        extension = ".py"
    else:
        _validate_javascript_source(draft.source)
        extension = ".test.ts" if draft.language == "typescript" else ".test.js"

    return ValidatedTestArtifact(
        test_id=draft.test_id,
        finding_id=draft.finding_id,
        snapshot_id=profile.snapshot_id,
        language=draft.language,
        framework=draft.framework,
        suggested_copy_destination=draft.suggested_target_path,
        source=draft.source,
        suggested_run_command=draft.suggested_run_command,
        extension=extension,
    )


def write_test_artifact(artifact: ValidatedTestArtifact, run_dir: Path) -> Path:
    """Write a reviewed draft and its unexecuted manifest within the run directory."""
    if not _SAFE_FINDING_ID.fullmatch(artifact.finding_id):
        raise TestArtifactPolicyError("finding ID is not safe for an artifact filename")

    tests_dir = run_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = tests_dir / f"{artifact.finding_id}{artifact.extension}"
    artifact_path.write_text(artifact.source, encoding="utf-8", newline="\n")

    manifest_path = run_dir / "test_manifest.json"
    artifacts = _load_manifest(manifest_path)
    record = {
        "finding_id": artifact.finding_id,
        "framework": artifact.framework,
        "snapshot_id": artifact.snapshot_id,
        "status": "unexecuted",
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


def _validate_metadata(draft: GeneratedTestDraft, profile: RepositoryProfile) -> None:
    if not draft.finding_id or not _SAFE_FINDING_ID.fullmatch(draft.finding_id):
        raise TestArtifactPolicyError("draft requires a safe finding ID")
    if not profile.profile_evidence_ids:
        raise TestArtifactPolicyError("repository profile requires signed evidence IDs")
    if draft.framework not in profile.test_frameworks:
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

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in _PYTHON_FORBIDDEN_MODULES for alias in node.names):
                raise TestArtifactPolicyError("Python draft imports a forbidden module")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in _PYTHON_FORBIDDEN_MODULES:
                raise TestArtifactPolicyError("Python draft imports a forbidden module")
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in _PYTHON_FORBIDDEN_CALLS:
                raise TestArtifactPolicyError("Python draft invokes a forbidden function")
            if call_name in {"open", "Path.write_text", "Path.write_bytes"}:
                raise TestArtifactPolicyError("Python draft writes to the target repository")
            if call_name.endswith((".write_text", ".write_bytes", ".unlink", ".mkdir")):
                raise TestArtifactPolicyError("Python draft writes to the target repository")


def _validate_javascript_source(source: str) -> None:
    for forbidden in _JAVASCRIPT_FORBIDDEN:
        if forbidden.search(source):
            raise TestArtifactPolicyError("JavaScript draft uses a forbidden capability")
    if re.search(r"\bfetch\s*\(", source) and not _has_mocked_fetch(source):
        raise TestArtifactPolicyError("JavaScript draft uses unmocked fetch")
    if re.search(r"\baxios\b", source) and not _has_mocked_axios(source):
        raise TestArtifactPolicyError("JavaScript draft uses unmocked axios")


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _has_mocked_fetch(source: str) -> bool:
    return bool(re.search(
        r"""(?:vi\.stubGlobal\(\s*['"]fetch['"]|global\.fetch\s*=|jest\.spyOn\(\s*global(?:This)?\s*,\s*['"]fetch['"])""",
        source,
    ))


def _has_mocked_axios(source: str) -> bool:
    return bool(re.search(r"""(?:vi|jest)\.mock\(\s*['"]axios['"]""", source))


def _is_absolute_path(path: str) -> bool:
    return path.startswith(("/", "\\")) or Path(path).is_absolute() or PureWindowsPath(path).is_absolute()


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
