from __future__ import annotations

import json
from pathlib import Path

import pytest

from saads_grill_agent.contracts import GeneratedTestDraft, RepositoryProfile
from saads_grill_agent.test_artifacts import (
    TestArtifactPolicyError,
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


def make_draft(
    *,
    source: str = "def test_regression():\n    assert True",
    language: str = "python",
    framework: str = "pytest",
    suggested_target_path: str = "tests/test_regression.py",
) -> GeneratedTestDraft:
    return GeneratedTestDraft(
        test_id="test-1",
        finding_id="finding-1",
        language=language,  # type: ignore[arg-type]
        framework=framework,  # type: ignore[arg-type]
        suggested_target_path=suggested_target_path,
        source=source,
        expected_failing_assertion="assert response.status_code == 400",
        mocked_dependencies=["app.client"],
        required_fixtures=["client"],
        suggested_run_command="pytest tests/test_regression.py",
    )


@pytest.mark.parametrize("source", [
    "import subprocess\nsubprocess.run(['curl', url])",
    "import requests\nrequests.post('https://target.example')",
    "from urllib.request import urlopen\nurlopen('https://target.example')",
    "import httpx\nhttpx.get('https://target.example')",
    "import os\nos.system('id')",
    "eval('1 + 1')",
    "exec('raise RuntimeError')",
])
def test_generated_test_rejects_python_external_or_process_access(source: str) -> None:
    with pytest.raises(TestArtifactPolicyError):
        validate_test_draft(make_draft(source=source), repository_profile())


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
        repository_profile(),
    )

    assert artifact.extension == ".py"
    assert artifact.snapshot_id == "snapshot-1"


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
        repository_profile([framework]),
    )

    assert artifact.framework == framework


@pytest.mark.parametrize(
    ("draft", "profile"),
    [
        (make_draft(framework="jest"), repository_profile(["pytest"])),
        (make_draft(suggested_target_path="/tmp/test.py"), repository_profile()),
        (make_draft(suggested_target_path=r"C:\target\test.py"), repository_profile()),
        (make_draft(source="open('app/main.py', 'w').write('changed')"), repository_profile()),
        (make_draft().model_copy(update={"finding_id": ""}), repository_profile()),
        (make_draft().model_copy(update={"finding_id": "../finding"}), repository_profile()),
        (make_draft(source="x" * (30 * 1024 + 1)), repository_profile()),
    ],
)
def test_generated_test_rejects_invalid_metadata_or_target_write(
    draft: GeneratedTestDraft, profile: RepositoryProfile,
) -> None:
    with pytest.raises(TestArtifactPolicyError):
        validate_test_draft(draft, profile)


def test_write_test_artifact_publishes_only_unexecuted_run_artifact(
    tmp_path: Path,
) -> None:
    artifact = validate_test_draft(make_draft(), repository_profile())

    path = write_test_artifact(artifact, tmp_path)

    assert path == tmp_path / "tests" / "finding-1.py"
    assert path.read_text(encoding="utf-8") == artifact.source
    manifest = json.loads((tmp_path / "test_manifest.json").read_text(encoding="utf-8"))
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
