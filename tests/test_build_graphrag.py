import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import httpx

from scripts.build_graphrag import (
    BuildError,
    _api_error,
    preflight_models,
    run_checked,
    single_build_lock,
    validate_corpus,
    validate_index,
)


def test_validate_corpus_requires_matching_minimum_counts(tmp_path: Path) -> None:
    (tmp_path / "input").mkdir()
    (tmp_path / "reports").mkdir()
    documents = [{"id": str(index), "text": "content"} for index in range(100)]
    (tmp_path / "input" / "_corpus.json").write_text(
        json.dumps(documents), encoding="utf-8"
    )
    pd.DataFrame({"id": range(100)}).to_csv(
        tmp_path / "reports" / "corpus_manifest.csv", index=False
    )

    assert validate_corpus(tmp_path) == {"documents": 100, "manifest_rows": 100}


def test_validate_index_rejects_partial_output(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    pd.DataFrame({"id": ["document-1"]}).to_parquet(output / "documents.parquet")

    with pytest.raises(BuildError, match="missing required parquet"):
        validate_index(tmp_path)


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


def test_preflight_uses_deepseek_for_completion_and_zhipu_for_embedding(
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
        "DEEPSEEK_API_KEY": "deepseek-key",
        "DEEPSEEK_API_BASE": "https://api.deepseek.com",
        "DEEPSEEK_CHAT_MODEL": "deepseek-v4-flash",
        "ZHIPU_API_KEY": "zhipu-key",
        "ZHIPU_API_BASE": "https://open.bigmodel.cn/api/paas/v4",
        "ZHIPU_EMBEDDING_MODEL": "embedding-3",
        "ZHIPU_EMBEDDING_DIMENSIONS": "2",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr("scripts.build_graphrag.httpx.Client", FakeClient)

    assert preflight_models() == {
        "completion_provider": "deepseek",
        "chat_model": "deepseek-v4-flash",
        "embedding_provider": "zhipu",
        "embedding_model": "embedding-3",
        "embedding_dimensions": 2,
    }
    assert requests[0] == {
        "url": "https://api.deepseek.com/chat/completions",
        "headers": {
            "Authorization": "Bearer deepseek-key",
            "Content-Type": "application/json",
        },
        "json": {
            "model": "deepseek-v4-flash",
            "messages": [
                {
                    "role": "user",
                    "content": "GraphRAG connectivity check. Reply with OK.",
                }
            ],
            "temperature": 0,
            "max_tokens": 16,
            "thinking": {"type": "disabled"},
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
