from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from saads_grill_agent.contracts import Finding, GeneratedTestDraft, RepositoryProfile
from saads_grill_agent.test_artifacts import (
    SnapshotObjection,
    TestArtifactPolicyError,
    TestArtifactStatus,
    ValidatedTestArtifact,
    collect_snapshot_objections,
    validate_test_draft,
    write_test_artifact,
)


def repository_profile(
    frameworks: list[str] | None = None,
) -> RepositoryProfile:
    return RepositoryProfile(
        snapshot_id="snapshot-1",
        model_provider="test",
        model_name="test-model",
        agent_framework="test-framework",
        frontend_roots=["web"],
        backend_roots=["app"],
        model_call_sites=["app/model.py"],
        prompt_assembly_sites=["app/prompt.py"],
        tool_definition_sites=["app/tools.py"],
        retrieval_and_ingestion_sites=["app/rag.py"],
        memory_sites=[],
        authn_authz_sites=["app/auth.py"],
        output_interpretation_sites=["app/output.py"],
        test_frameworks=frameworks or ["pytest"],
        profile_evidence_ids=["code-profile-1"],
        supplied_profile_conflicts=[],
    )


def make_finding(
    *,
    finding_id: str = "finding-1",
    code_evidence_ids: list[str] | None = None,
    graph_evidence_ids: list[str] | None = None,
) -> Finding:
    return Finding(
        finding_id=finding_id,
        hypothesis_id="hyp-1",
        severity="high",
        confidence="medium",
        root_cause="Untrusted context concatenated with trusted instructions.",
        attack_path=["attacker controls retrieved context"],
        impact="Instruction hijack.",
        preconditions=["retrieval returns attacker content"],
        code_evidence_ids=(
            ["code-1"] if code_evidence_ids is None else code_evidence_ids
        ),
        graph_evidence_ids=(
            [] if graph_evidence_ids is None else graph_evidence_ids
        ),
        remediation="Separate provenance of trusted and untrusted context.",
    )


def make_draft(
    *,
    source: str = "def test_regression():\n    assert True",
    language: str = "python",
    framework: str = "pytest",
    suggested_target_path: str = "tests/test_regression.py",
    finding_id: str = "finding-1",
    mocked_dependencies: list[str] | None = None,
    required_fixtures: list[str] | None = None,
) -> GeneratedTestDraft:
    return GeneratedTestDraft(
        test_id="test-1",
        finding_id=finding_id,
        language=language,  # type: ignore[arg-type]
        framework=framework,  # type: ignore[arg-type]
        suggested_target_path=suggested_target_path,
        source=source,
        expected_failing_assertion="assert response.status_code == 400",
        mocked_dependencies=mocked_dependencies or ["app.client"],
        required_fixtures=required_fixtures or ["client"],
        suggested_run_command="pytest tests/test_regression.py",
    )


@pytest.mark.parametrize("source", [
    "import subprocess\nsubprocess.run(['curl', url])",
    "import requests\nrequests.post('https://target.example')",
    "from urllib.request import urlopen\nurlopen('https://target.example')",
    "import httpx\nhttpx.get('https://target.example')",
    "import os\nos.system('id')",
    "import os as safe\nsafe.system('id')",
    "from os import system as boom\nboom('id')",
    "eval('1 + 1')",
    "exec('raise RuntimeError')",
    "from pathlib import Path\nPath('app/main.py').write_text('changed')",
    "from pathlib import Path\nPath('app/main.py').write_bytes(b'changed')",
    "from pathlib import Path\nPath('app/tmp').unlink()",
    "from pathlib import Path\nPath('app/tmp').rmdir()",
    "open('app/main.py', 'w').write('changed')",
])
def test_generated_test_rejects_python_external_or_process_access(source: str) -> None:
    with pytest.raises(TestArtifactPolicyError):
        validate_test_draft(make_draft(source=source), make_finding(), repository_profile())


@pytest.mark.parametrize("source", [
    "const cp = require('child_process'); cp.exec('id')",
    "import net from 'net'; net.createConnection(80)",
    "import dgram from 'dgram'; dgram.createSocket('udp4')",
    "await fetch('https://target.example')",
    "axios.get('https://target.example')",
    "const module = await import('./target')",
    "process.execPath",
])
def test_generated_test_rejects_javascript_external_or_process_access(source: str) -> None:
    with pytest.raises(TestArtifactPolicyError):
        validate_test_draft(
            make_draft(source=source, language="typescript", framework="vitest"),
            make_finding(),
            repository_profile(["vitest"]),
        )


def test_generated_test_accepts_pytest_fastapi_testclient_override() -> None:
    artifact = validate_test_draft(
        make_draft(source=(
            "from fastapi.testclient import TestClient\n"
            "from app.main import app\n\n"
            "def test_regression():\n"
            "    app.dependency_overrides[get_service] = lambda: fake_service\n"
            "    client = TestClient(app)\n"
            "    assert client.get('/items').status_code == 400"
        )),
        make_finding(),
        repository_profile(),
    )

    assert artifact.extension == ".py"
    assert artifact.snapshot_id == "snapshot-1"
    assert artifact.status is TestArtifactStatus.UNEXECUTED


@pytest.mark.parametrize(
    ("framework", "source"),
    [
        (
            "vitest",
            "import { vi, test } from 'vitest'\n"
            "vi.stubGlobal('fetch', vi.fn())\n"
            "test('regression', () => expect(fetch).toHaveBeenCalled())",
        ),
        (
            "jest",
            "global.fetch = jest.fn()\n"
            "test('regression', () => expect(fetch).toHaveBeenCalled())",
        ),
    ],
)
def test_generated_test_accepts_mocked_fetch(
    framework: str, source: str,
) -> None:
    artifact = validate_test_draft(
        make_draft(source=source, language="typescript", framework=framework),
        make_finding(),
        repository_profile([framework]),
    )

    assert artifact.framework == framework


@pytest.mark.parametrize(
    ("draft", "finding", "profile"),
    [
        (make_draft(framework="jest"), make_finding(), repository_profile(["pytest"])),
        (make_draft(suggested_target_path="/tmp/test.py"), make_finding(), repository_profile()),
        (make_draft(suggested_target_path=r"C:\target\test.py"), make_finding(), repository_profile()),
        (make_draft(source="open('app/main.py', 'w').write('changed')"), make_finding(), repository_profile()),
        (make_draft().model_copy(update={"finding_id": ""}), make_finding(), repository_profile()),
        (make_draft().model_copy(update={"finding_id": "../finding"}), make_finding(), repository_profile()),
        (make_draft(source="x" * (30 * 1024 + 1)), make_finding(), repository_profile()),
        (make_draft(), None, repository_profile()),
        (make_draft(finding_id="finding-other"), make_finding(), repository_profile()),
    ],
)
def test_generated_test_rejects_invalid_metadata_or_target_write(
    draft: GeneratedTestDraft,
    finding: Finding | None,
    profile: RepositoryProfile,
) -> None:
    with pytest.raises(TestArtifactPolicyError):
        validate_test_draft(draft, finding, profile)


def test_generated_test_rejects_unconfirmed_finding() -> None:
    unconfirmed = SimpleNamespace(
        finding_id="finding-1",
        status="rejected",
        code_evidence_ids=["code-1"],
        graph_evidence_ids=[],
    )
    with pytest.raises(TestArtifactPolicyError, match="not confirmed"):
        validate_test_draft(make_draft(), unconfirmed, repository_profile())  # type: ignore[arg-type]


def test_generated_test_rejects_finding_without_signed_evidence() -> None:
    finding = Finding.model_construct(
        finding_id="finding-1",
        hypothesis_id="hyp-1",
        severity="high",
        confidence="medium",
        root_cause="x",
        attack_path=["a"],
        impact="y",
        preconditions=[],
        code_evidence_ids=[],
        graph_evidence_ids=[],
        remediation="z",
        generated_test_ids=[],
    )
    with pytest.raises(TestArtifactPolicyError, match="signed evidence"):
        validate_test_draft(make_draft(), finding, repository_profile())


def test_write_test_artifact_publishes_only_unexecuted_run_artifact(
    tmp_path: Path,
) -> None:
    draft = make_draft()
    finding = make_finding()
    profile = repository_profile()
    run_dir = tmp_path / "run"
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    run_dir.mkdir()

    path = write_test_artifact(draft, finding, profile, run_dir, target_repo)

    assert path == run_dir / "tests" / "finding-1.py"
    assert path.read_text(encoding="utf-8") == draft.source
    manifest = json.loads((run_dir / "test_manifest.json").read_text(encoding="utf-8"))
    assert manifest == {
        "artifacts": [{
            "finding_id": "finding-1",
            "framework": "pytest",
            "snapshot_id": "snapshot-1",
            "status": "unexecuted",
            "suggested_copy_destination": "tests/test_regression.py",
            "suggested_run_command": "pytest tests/test_regression.py",
            "test_id": "test-1",
        }]
    }


def test_write_test_artifact_refuses_target_repo_containment(
    tmp_path: Path,
) -> None:
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    # Intentionally place the run directory inside the target repository.
    run_dir = target_repo / "audit-run"
    run_dir.mkdir()

    with pytest.raises(TestArtifactPolicyError, match="target repository"):
        write_test_artifact(
            make_draft(),
            make_finding(),
            repository_profile(),
            run_dir,
            target_repo,
        )


def test_write_test_artifact_revalidates_and_rejects_unsafe_draft(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    target_repo = tmp_path / "target"
    run_dir.mkdir()
    target_repo.mkdir()

    with pytest.raises(TestArtifactPolicyError):
        write_test_artifact(
            make_draft(source="import os as safe\nsafe.system('id')"),
            make_finding(),
            repository_profile(),
            run_dir,
            target_repo,
        )
    assert not (run_dir / "tests").exists()


def test_validated_artifact_requires_seal_for_trust() -> None:
    forged = ValidatedTestArtifact(
        test_id="test-1",
        finding_id="finding-1",
        snapshot_id="snapshot-1",
        language="python",
        framework="pytest",
        suggested_copy_destination="tests/test_regression.py",
        source="def test_regression():\n    assert True",
        suggested_run_command="pytest",
        extension=".py",
    )
    assert forged._seal is None
    sealed = validate_test_draft(make_draft(), make_finding(), repository_profile())
    assert sealed._seal is not None


def test_collect_snapshot_objections_flags_missing_imports_and_paths() -> None:
    draft = make_draft(
        source=(
            "from app.main import app\n"
            "from app.missing_mod import helper\n\n"
            "def test_regression():\n"
            "    assert True\n"
        ),
        mocked_dependencies=["app.missing_dep"],
        required_fixtures=["fixtures/missing_fixture.py"],
        suggested_target_path="app/absent_dir/test_regression.py",
    )
    paths = {
        "app/main.py",
        "app/client.py",
        "tests/conftest.py",
    }

    objections = collect_snapshot_objections(draft, paths)

    kinds = {(item.kind, item.reference) for item in objections}
    assert ("missing_import", "app.missing_mod") in kinds
    assert ("missing_import", "app.missing_dep") in kinds
    assert ("missing_fixture", "fixtures/missing_fixture.py") in kinds
    assert ("missing_path", "app/absent_dir/test_regression.py") in kinds
    assert all(isinstance(item, SnapshotObjection) for item in objections)


def test_collect_snapshot_objections_accepts_present_imports() -> None:
    draft = make_draft(
        source=(
            "from app.main import app\n\n"
            "def test_regression():\n"
            "    assert True\n"
        ),
        mocked_dependencies=["app.client"],
        required_fixtures=["client"],
        suggested_target_path="tests/test_regression.py",
    )
    paths = {"app/main.py", "app/client.py", "tests/conftest.py"}

    assert collect_snapshot_objections(draft, paths) == []


def test_generation_failed_status_is_exposed() -> None:
    assert TestArtifactStatus.GENERATION_FAILED.value == "generation_failed"
    assert TestArtifactStatus.UNEXECUTED.value == "unexecuted"
