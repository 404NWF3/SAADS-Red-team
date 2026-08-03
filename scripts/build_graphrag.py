from __future__ import annotations

import argparse
import csv
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

from llm_defense_graphrag.summary_corpus import prepare_summary_corpus


REQUIRED_PARQUETS = (
    "documents",
    "text_units",
    "entities",
    "relationships",
    "communities",
    "community_reports",
    "entity_alignment",
)
FORBIDDEN_ENTITY_ALIASES = {
    "AI BOM",
    "HUGGINGFACE",
    "LARGE LANGUAGE MODEL (LLM)",
    "FINE-TUNING",
    "FINETUNING",
}


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
        help="Check corpus, GLM completion, and Zhipu embedding resources.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Archive the current output and build a new index from an empty output.",
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
        "ZAI_API_KEY",
        "ZAI_CHAT_MODEL",
        "ZHIPU_API_KEY",
        "ZHIPU_API_BASE",
        "ZHIPU_EMBEDDING_MODEL",
        "ZHIPU_EMBEDDING_DIMENSIONS",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise BuildError(f"Missing required environment variables: {', '.join(missing)}")


def validate_corpus(root: Path, minimum: int = 100) -> dict[str, int]:
    corpus_path = root / "summary_input" / "summary_corpus.json"
    if not corpus_path.is_file():
        raise BuildError(
            "Summary corpus is missing; run scripts/prepare_summary_corpus.py first."
        )
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    if not isinstance(corpus, list):
        raise BuildError(f"Expected a JSON array in {corpus_path}.")
    if len(corpus) < minimum:
        raise BuildError(
            f"Corpus is below the {minimum}-document gate: json={len(corpus)}."
        )
    for index, document in enumerate(corpus, start=1):
        expected = {
            "id": f"summary-{index:06d}",
            "title": f"Summary {index:06d}",
        }
        if not isinstance(document, dict) or set(document) != {"id", "title", "text"}:
            raise BuildError(
                f"Summary corpus row {index} must contain only id, title, and text."
            )
        if document["id"] != expected["id"] or document["title"] != expected["title"]:
            raise BuildError(f"Summary corpus row {index} has non-synthetic structure.")
        if not isinstance(document["text"], str) or not document["text"].strip():
            raise BuildError(f"Summary corpus row {index} has empty text.")
    return {"documents": len(corpus), "summary_rows": len(corpus)}


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
    completion_base = os.environ["ZHIPU_API_BASE"].rstrip("/")
    completion_headers = {
        "Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
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
                "model": os.environ["ZAI_CHAT_MODEL"],
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
        "completion_provider": "zai",
        "chat_model": os.environ["ZAI_CHAT_MODEL"],
        "embedding_provider": "zhipu",
        "embedding_model": os.environ["ZHIPU_EMBEDDING_MODEL"],
        "embedding_dimensions": dimensions,
    }


def prepare_fresh_output(root: Path) -> Path | None:
    root = root.resolve()
    output = (root / "output").resolve()
    backup_root = (root / "backups").resolve()
    if output.parent != root or backup_root.parent != root:
        raise BuildError("Fresh output paths escaped the project root.")

    backup: Path | None = None
    if output.exists():
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup = backup_root / f"output-{stamp}"
        output.rename(backup)
    output.mkdir(parents=True, exist_ok=False)
    return backup


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


def validate_summary_provenance(root: Path) -> dict[str, int]:
    source_path = root / "data" / "items_20260713T095333Z.csv"
    corpus_path = root / "summary_input" / "summary_corpus.json"
    documents_path = root / "output" / "documents.parquet"

    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "summary" not in reader.fieldnames:
            raise BuildError(f"Source CSV is missing the summary column: {source_path}")
        source_summaries = [
            (row.get("summary") or "").strip()
            for row in reader
        ]

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    indexed = pd.read_parquet(documents_path)
    if len(source_summaries) != len(corpus) or len(corpus) != len(indexed):
        raise BuildError(
            "Summary provenance row counts differ: "
            f"source={len(source_summaries)}, corpus={len(corpus)}, "
            f"indexed={len(indexed)}."
        )

    indexed_by_id = {
        str(row["id"]): row
        for row in indexed.to_dict(orient="records")
    }
    exact_matches = 0
    for position, summary_text in enumerate(source_summaries, start=1):
        expected = {
            "id": f"summary-{position:06d}",
            "title": f"Summary {position:06d}",
            "text": summary_text,
        }
        corpus_row = corpus[position - 1]
        indexed_row = indexed_by_id.get(expected["id"])
        if (
            corpus_row != expected
            or indexed_row is None
            or indexed_row.get("title") != expected["title"]
            or indexed_row.get("text") != expected["text"]
            or indexed_row.get("raw_data") != expected
        ):
            raise BuildError(
                f"Summary row {position} does not exactly match the final indexed document."
            )
        exact_matches += 1

    return {
        "source_summary_rows": len(source_summaries),
        "corpus_rows": len(corpus),
        "indexed_documents": len(indexed),
        "exact_matches": exact_matches,
    }


def validate_entity_alignment(root: Path) -> dict[str, int]:
    output = root / "output"
    entities = pd.read_parquet(output / "entities.parquet")
    relationships = pd.read_parquet(output / "relationships.parquet")
    audit = pd.read_parquet(output / "entity_alignment.parquet")

    titles = entities["title"].astype(str)
    forbidden = sorted(set(titles).intersection(FORBIDDEN_ENTITY_ALIASES))
    if forbidden:
        raise BuildError(
            f"Index contains forbidden aliases: {', '.join(forbidden)}"
        )
    duplicates = titles[titles.duplicated()].unique().tolist()
    if duplicates:
        raise BuildError(
            f"Canonical entity titles are not unique: {', '.join(duplicates[:10])}"
        )

    title_set = set(titles)
    endpoints = set(relationships["source"].astype(str)).union(
        relationships["target"].astype(str)
    )
    missing = sorted(endpoints - title_set)
    if missing:
        raise BuildError(
            f"Relationships reference missing canonical entities: {', '.join(missing[:10])}"
        )

    self_loops = int(
        (
            relationships["source"].astype(str)
            == relationships["target"].astype(str)
        ).sum()
    )
    if self_loops:
        raise BuildError(f"Alignment output contains {self_loops} self-loop relations.")

    required_audit_columns = {
        "source_title",
        "source_type",
        "canonical_title",
        "canonical_type",
        "method",
        "confidence",
        "reason",
    }
    missing_columns = required_audit_columns - set(audit.columns)
    if missing_columns:
        raise BuildError(
            f"Entity alignment audit is missing columns: {sorted(missing_columns)}"
        )
    audit_targets = set(audit["canonical_title"].astype(str))
    missing_audit_targets = sorted(audit_targets - title_set)
    if missing_audit_targets:
        raise BuildError(
            "Entity alignment audit references missing canonical titles: "
            + ", ".join(missing_audit_targets[:10])
        )

    changed = int(
        (
            (audit["source_title"].astype(str) != audit["canonical_title"].astype(str))
            | (audit["source_type"].astype(str) != audit["canonical_type"].astype(str))
        ).sum()
    )
    review_required = int(
        audit["method"].astype(str).str.contains("review_required").sum()
    )
    if review_required:
        raise BuildError(
            f"Entity alignment has {review_required} unresolved review decisions."
        )
    return {
        "audit_rows": len(audit),
        "changed_entities": changed,
        "review_required": review_required,
        "self_loops": self_loops,
    }


def write_entity_alignment_report(
    root: Path, summary: dict[str, int]
) -> None:
    audit = pd.read_parquet(root / "output" / "entity_alignment.parquet")
    method_counts = {
        str(method): int(count)
        for method, count in audit["method"].value_counts().sort_index().items()
    }
    decisions = json.loads(
        audit.to_json(orient="records", force_ascii=False)
    )
    report_path = root / "reports" / "entity_alignment.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "method_counts": method_counts,
                "decisions": decisions,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


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
        corpus_stats = prepare_summary_corpus(
            root / "data" / "items_20260713T095333Z.csv",
            root / "summary_input" / "summary_corpus.json",
        )
        summary["source"] = {
            "csv": "data/items_20260713T095333Z.csv",
            "field": "summary",
            "total_rows": corpus_stats.total_rows,
            "written_rows": corpus_stats.written_rows,
            "empty_rows": corpus_stats.empty_rows,
        }
        summary["corpus"] = validate_corpus(root)
        if args.preflight_only:
            summary["models"] = preflight_models()
            summary["status"] = "preflight_ok"
            return
        if not args.fresh:
            raise BuildError(
                "A full rebuild requires --fresh so the previous index cannot be reused."
            )

        with single_build_lock(root):
            summary["models"] = preflight_models()
            backup = prepare_fresh_output(root)
            summary["previous_output_backup"] = (
                str(backup.relative_to(root)) if backup is not None else None
            )
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
            summary["summary_provenance"] = validate_summary_provenance(root)
            alignment = validate_entity_alignment(root)
            summary["entity_alignment"] = alignment
            write_entity_alignment_report(root, alignment)
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
