import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import httpx

from scripts.build_graphrag import (
    BuildError,
    _api_error,
    prepare_fresh_output,
    preflight_models,
    run_checked,
    single_build_lock,
    validate_corpus,
    validate_entity_alignment,
    validate_index,
    validate_summary_provenance,
    write_entity_alignment_report,
)


def test_validate_corpus_requires_summary_only_document_shape(
    tmp_path: Path,
) -> None:
    (tmp_path / "summary_input").mkdir()
    documents = [
        {
            "id": f"summary-{index:06d}",
            "title": f"Summary {index:06d}",
            "text": f"Summary content {index}.",
        }
        for index in range(1, 101)
    ]
    (tmp_path / "summary_input" / "summary_corpus.json").write_text(
        json.dumps(documents), encoding="utf-8"
    )

    assert validate_corpus(tmp_path) == {
        "documents": 100,
        "summary_rows": 100,
    }


def test_validate_summary_provenance_checks_final_documents_row_by_row(
    tmp_path: Path,
) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "summary_input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "data" / "items_20260713T095333Z.csv").write_text(
        "item_id,title,summary,source_uri\n"
        "forbidden-id,Forbidden title,Allowed summary.,https://forbidden.test\n",
        encoding="utf-8-sig",
    )
    corpus = [
        {
            "id": "summary-000001",
            "title": "Summary 000001",
            "text": "Allowed summary.",
        }
    ]
    (tmp_path / "summary_input" / "summary_corpus.json").write_text(
        json.dumps(corpus), encoding="utf-8"
    )
    pd.DataFrame(
        {
            "id": ["summary-000001"],
            "title": ["Summary 000001"],
            "text": ["Allowed summary."],
            "raw_data": [corpus[0]],
        }
    ).to_parquet(tmp_path / "output" / "documents.parquet")

    assert validate_summary_provenance(tmp_path) == {
        "source_summary_rows": 1,
        "corpus_rows": 1,
        "indexed_documents": 1,
        "exact_matches": 1,
    }

    indexed = pd.read_parquet(tmp_path / "output" / "documents.parquet")
    indexed.loc[0, "text"] = "Forbidden title"
    indexed.to_parquet(tmp_path / "output" / "documents.parquet")
    with pytest.raises(BuildError, match="does not exactly match"):
        validate_summary_provenance(tmp_path)


def test_prepare_fresh_output_archives_existing_index(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "old-marker.txt").write_text("old index", encoding="utf-8")

    backup = prepare_fresh_output(tmp_path)

    assert backup is not None
    assert backup.parent == tmp_path / "backups"
    assert (backup / "old-marker.txt").read_text(encoding="utf-8") == "old index"
    assert output.is_dir()
    assert list(output.iterdir()) == []


def test_validate_index_rejects_partial_output(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    pd.DataFrame({"id": ["document-1"]}).to_parquet(output / "documents.parquet")

    with pytest.raises(BuildError, match="missing required parquet"):
        validate_index(tmp_path)


def test_validate_entity_alignment_checks_aliases_and_endpoints(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    pd.DataFrame(
        {
            "title": ["AIBOM", "LLM"],
            "type": ["DEFENSE_CONTROL", "COMPONENT"],
        }
    ).to_parquet(output / "entities.parquet")
    pd.DataFrame(
        {
            "source": ["AIBOM"],
            "target": ["LLM"],
        }
    ).to_parquet(output / "relationships.parquet")
    pd.DataFrame(
        {
            "source_title": ["AI BOM", "LLM"],
            "source_type": ["DEFENSE_CONTROL", "COMPONENT"],
            "canonical_title": ["AIBOM", "LLM"],
            "canonical_type": ["DEFENSE_CONTROL", "COMPONENT"],
            "method": ["registry", "identity"],
            "confidence": [1.0, 1.0],
            "reason": ["registry", "identity"],
        }
    ).to_parquet(output / "entity_alignment.parquet")

    metrics = validate_entity_alignment(tmp_path)
    assert metrics == {
        "audit_rows": 2,
        "changed_entities": 1,
        "review_required": 0,
        "self_loops": 0,
    }
    write_entity_alignment_report(tmp_path, metrics)
    report = json.loads(
        (tmp_path / "reports" / "entity_alignment.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["summary"] == metrics
    assert report["method_counts"] == {"identity": 1, "registry": 1}
    assert len(report["decisions"]) == 2

    entities = pd.read_parquet(output / "entities.parquet")
    entities.loc[0, "title"] = "AI BOM"
    entities.to_parquet(output / "entities.parquet")

    with pytest.raises(BuildError, match="forbidden aliases"):
        validate_entity_alignment(tmp_path)


def test_single_build_lock_rejects_a_second_builder(tmp_path: Path) -> None:
    lock_path = tmp_path / "logs" / "graphrag-build.lock"

    with single_build_lock(tmp_path):
        assert lock_path.is_file()
        with pytest.raises(BuildError, match="Another build lock exists"):
            with single_build_lock(tmp_path):
                pass

    assert not lock_path.exists()


def test_balance_error_has_stable_chinese_diagnostic() -> None:
    response = httpx.Response(
        429,
        json={"error": {"code": "1113", "message": "garbled upstream text"}},
    )

    assert _api_error(response) == "HTTP 429, code 1113: 余额不足或无可用资源包，请充值。"


def test_preflight_uses_glm_for_completion_and_zhipu_for_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict[str, object]] = []

    class FakeResponse:
        is_success = True

        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def json(self) -> dict[str, object]:
            return self._payload

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            assert timeout == 60.0

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def post(
            self, url: str, *, headers: dict[str, str], json: dict[str, object]
        ) -> FakeResponse:
            requests.append({"url": url, "headers": headers, "json": json})
            if url.endswith("/embeddings"):
                return FakeResponse({"data": [{"embedding": [0.0, 0.0]}]})
            return FakeResponse({"choices": [{"message": {"content": "OK"}}]})

    environment = {
        "ZAI_API_KEY": "zai-key",
        "ZAI_CHAT_MODEL": "glm-4.5-air",
        "ZHIPU_API_KEY": "zhipu-key",
        "ZHIPU_API_BASE": "https://open.bigmodel.cn/api/paas/v4",
        "ZHIPU_EMBEDDING_MODEL": "embedding-3",
        "ZHIPU_EMBEDDING_DIMENSIONS": "2",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr("scripts.build_graphrag.httpx.Client", FakeClient)

    assert preflight_models() == {
        "completion_provider": "zai",
        "chat_model": "glm-4.5-air",
        "embedding_provider": "zhipu",
        "embedding_model": "embedding-3",
        "embedding_dimensions": 2,
    }
    assert requests[0] == {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "headers": {
            "Authorization": "Bearer zai-key",
            "Content-Type": "application/json",
        },
        "json": {
            "model": "glm-4.5-air",
            "messages": [
                {
                    "role": "user",
                    "content": "GraphRAG connectivity check. Reply with OK.",
                }
            ],
            "temperature": 0,
            "max_tokens": 16,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
        },
    }
    assert requests[1]["url"] == "https://open.bigmodel.cn/api/paas/v4/embeddings"
    assert requests[1]["headers"] == {
        "Authorization": "Bearer zhipu-key",
        "Content-Type": "application/json",
    }


def test_run_checked_forces_utf8_for_child_processes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def fake_run(
        command: list[str], *, cwd: Path, check: bool, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        captured.update({"command": command, "cwd": cwd, "check": check, "env": env})
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("scripts.build_graphrag.subprocess.run", fake_run)

    run_checked(["graphrag", "index"], tmp_path)

    assert captured["command"] == ["graphrag", "index"]
    assert captured["cwd"] == tmp_path
    assert captured["check"] is False
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["PYTHONUTF8"] == "1"
    assert environment["PYTHONIOENCODING"] == "utf-8"
