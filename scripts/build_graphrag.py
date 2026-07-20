from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import httpx
import pandas as pd
from dotenv import load_dotenv


REQUIRED_PARQUETS = (
    "documents",
    "text_units",
    "entities",
    "relationships",
    "communities",
    "community_reports",
)


class BuildError(RuntimeError):
    """A user-actionable GraphRAG build failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build, validate, analyze, and smoke-test llm-defense-graphrag."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Check corpus, DeepSeek completion, and Zhipu embedding resources.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_project_environment(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.is_file():
        raise BuildError(f"Missing {env_path}; copy .env.example and configure it first.")
    load_dotenv(env_path, override=False)
    required = (
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_API_BASE",
        "DEEPSEEK_CHAT_MODEL",
        "ZHIPU_API_KEY",
        "ZHIPU_API_BASE",
        "ZHIPU_EMBEDDING_MODEL",
        "ZHIPU_EMBEDDING_DIMENSIONS",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise BuildError(f"Missing required environment variables: {', '.join(missing)}")


def validate_corpus(root: Path, minimum: int = 100) -> dict[str, int]:
    corpus_path = root / "input" / "_corpus.json"
    manifest_path = root / "reports" / "corpus_manifest.csv"
    if not corpus_path.is_file() or not manifest_path.is_file():
        raise BuildError("Corpus or manifest is missing; run scripts/collect_corpus.py first.")
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    if not isinstance(corpus, list):
        raise BuildError(f"Expected a JSON array in {corpus_path}.")
    manifest = pd.read_csv(manifest_path)
    if len(corpus) < minimum or len(manifest) < minimum:
        raise BuildError(
            f"Corpus is below the {minimum}-document gate: "
            f"json={len(corpus)}, manifest={len(manifest)}."
        )
    if len(corpus) != len(manifest):
        raise BuildError(
            f"Corpus and manifest counts differ: json={len(corpus)}, manifest={len(manifest)}."
        )
    return {"documents": len(corpus), "manifest_rows": len(manifest)}


def _api_error(response: httpx.Response) -> str:
    try:
        error = response.json().get("error", {})
        code = str(error.get("code"))
        message = error.get("message")
        if code == "1113":
            message = "余额不足或无可用资源包，请充值。"
        return f"HTTP {response.status_code}, code {code}: {message}"
    except ValueError:
        return f"HTTP {response.status_code}: non-JSON response"


def preflight_models() -> dict[str, object]:
    completion_base = os.environ["DEEPSEEK_API_BASE"].rstrip("/")
    completion_headers = {
        "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json",
    }
    embedding_base = os.environ["ZHIPU_API_BASE"].rstrip("/")
    embedding_headers = {
        "Authorization": f"Bearer {os.environ['ZHIPU_API_KEY']}",
        "Content-Type": "application/json",
    }
    dimensions = int(os.environ["ZHIPU_EMBEDDING_DIMENSIONS"])
    with httpx.Client(timeout=60.0) as client:
        completion = client.post(
            f"{completion_base}/chat/completions",
            headers=completion_headers,
            json={
                "model": os.environ["DEEPSEEK_CHAT_MODEL"],
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
        )
        if not completion.is_success:
            raise BuildError(f"Completion model unavailable ({_api_error(completion)}).")

        embedding = client.post(
            f"{embedding_base}/embeddings",
            headers=embedding_headers,
            json={
                "model": os.environ["ZHIPU_EMBEDDING_MODEL"],
                "input": ["GraphRAG connectivity check"],
                "dimensions": dimensions,
            },
        )
        if not embedding.is_success:
            raise BuildError(f"Embedding model unavailable ({_api_error(embedding)}).")
        vector = embedding.json()["data"][0]["embedding"]
        if len(vector) != dimensions:
            raise BuildError(
                f"Embedding dimension mismatch: expected {dimensions}, received {len(vector)}."
            )
    return {
        "completion_provider": "deepseek",
        "chat_model": os.environ["DEEPSEEK_CHAT_MODEL"],
        "embedding_provider": "zhipu",
        "embedding_model": os.environ["ZHIPU_EMBEDDING_MODEL"],
        "embedding_dimensions": dimensions,
    }


@contextmanager
def single_build_lock(root: Path) -> Iterator[None]:
    lock_path = root / "logs" / "graphrag-build.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        details = lock_path.read_text(encoding="utf-8", errors="replace").strip()
        raise BuildError(
            f"Another build lock exists at {lock_path}. Inspect the recorded process first: {details}"
        ) from exc
    try:
        os.write(
            descriptor,
            json.dumps({"pid": os.getpid(), "started_at": utc_now()}).encode("utf-8"),
        )
        os.close(descriptor)
        yield
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        lock_path.unlink(missing_ok=True)


def find_executable(root: Path, name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    local = root / ".venv" / ("Scripts" if os.name == "nt" else "bin") / f"{name}{suffix}"
    if local.is_file():
        return str(local)
    executable = shutil.which(name)
    if executable is None:
        raise BuildError(f"Executable '{name}' not found; run 'uv sync --dev'.")
    return executable


def run_checked(command: list[str], root: Path) -> None:
    print(f"running: {' '.join(command)}", flush=True)
    child_environment = os.environ.copy()
    # GraphRAG may print source text containing characters such as ®. Windows
    # otherwise inherits a GBK console encoding and can fail after a completed
    # workflow while rendering its result object.
    child_environment["PYTHONUTF8"] = "1"
    child_environment["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        env=child_environment,
    )
    if completed.returncode != 0:
        raise BuildError(
            f"Command failed with exit code {completed.returncode}: {' '.join(command)}"
        )


def validate_index(root: Path) -> dict[str, int]:
    output = root / "output"
    missing = [name for name in REQUIRED_PARQUETS if not (output / f"{name}.parquet").is_file()]
    if missing:
        raise BuildError(f"Index is missing required parquet artifacts: {', '.join(missing)}")
    rows = {
        name: len(pd.read_parquet(output / f"{name}.parquet"))
        for name in REQUIRED_PARQUETS
    }
    empty = [name for name, count in rows.items() if count == 0]
    if empty:
        raise BuildError(f"Index contains empty required artifacts: {', '.join(empty)}")
    lancedb = output / "lancedb"
    if not lancedb.is_dir() or not any(lancedb.rglob("*")):
        raise BuildError("Index is missing the populated output/lancedb vector store.")
    return rows


def write_summary(root: Path, summary: dict[str, object]) -> None:
    path = root / "reports" / "build_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    started = time.perf_counter()
    summary: dict[str, object] = {
        "status": "running",
        "started_at": utc_now(),
        "root": str(root),
    }
    try:
        load_project_environment(root)
        summary["corpus"] = validate_corpus(root)
        if args.preflight_only:
            summary["models"] = preflight_models()
            summary["status"] = "preflight_ok"
            return

        with single_build_lock(root):
            summary["models"] = preflight_models()
            python = find_executable(root, "python")
            run_checked(
                [
                    python,
                    "scripts/graphrag_cli.py",
                    "index",
                    "--root",
                    str(root),
                    "--method",
                    "standard",
                    "--verbose",
                    "--skip-validation",
                ],
                root,
            )
            summary["index_rows"] = validate_index(root)
            run_checked([python, "scripts/analyze_graph.py"], root)
            run_checked([python, "scripts/evaluate_queries.py", "--smoke"], root)
            summary["status"] = "complete"
    except BuildError as exc:
        summary["status"] = "blocked" if "code 1113" in str(exc) else "failed"
        summary["error"] = str(exc)
        raise SystemExit(str(exc)) from exc
    finally:
        summary["finished_at"] = utc_now()
        summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        write_summary(root, summary)


if __name__ == "__main__":
    main()
