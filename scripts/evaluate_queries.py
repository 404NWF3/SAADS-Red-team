from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml


METHODS = ("basic", "local", "global", "drift")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and record GraphRAG evaluation queries.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--questions", type=Path, default=Path("eval/questions.yaml"))
    parser.add_argument("--output", type=Path, default=Path("reports/query_evaluation.jsonl"))
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run only the first question for each method.",
    )
    parser.add_argument("--question-id", action="append", default=[])
    return parser.parse_args()


def load_questions(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    questions = data.get("questions", [])
    checks = data.get("manual_checks", [])
    if not questions:
        raise ValueError(f"No questions found in {path}")
    invalid = [item for item in questions if item.get("method") not in METHODS]
    if invalid:
        raise ValueError(f"Questions contain unsupported methods: {invalid}")
    return questions, checks


def select_questions(
    questions: list[dict[str, str]], smoke: bool, question_ids: list[str]
) -> list[dict[str, str]]:
    if question_ids:
        requested = set(question_ids)
        selected = [item for item in questions if item["id"] in requested]
        missing = requested - {item["id"] for item in selected}
        if missing:
            raise ValueError(f"Unknown question ids: {sorted(missing)}")
        return selected
    if not smoke:
        return questions
    return [next(item for item in questions if item["method"] == method) for method in METHODS]


def run_query(python: str, root: Path, item: dict[str, str]) -> dict[str, object]:
    command = [
        python,
        "scripts/graphrag_cli.py",
        "query",
        "--root",
        str(root),
        "--method",
        item["method"],
        "--response-type",
        "Multiple Paragraphs with source citations",
        item["question"],
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "id": item["id"],
        "method": item["method"],
        "question": item["question"],
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "answer": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    questions_path = (root / args.questions).resolve() if not args.questions.is_absolute() else args.questions
    output_path = (root / args.output).resolve() if not args.output.is_absolute() else args.output
    questions, manual_checks = load_questions(questions_path)
    selected = select_questions(questions, args.smoke, args.question_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in selected:
            result = run_query(sys.executable, root, item)
            result["manual_checks"] = {check: None for check in manual_checks}
            results.append(result)
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(
                f"{result['id']}: returncode={result['returncode']} "
                f"elapsed={result['elapsed_seconds']}s"
            )

    summary = {
        "questions_defined": len(questions),
        "questions_run": len(results),
        "successful": sum(result["returncode"] == 0 for result in results),
        "failed": sum(result["returncode"] != 0 for result in results),
        "methods_run": sorted({str(result["method"]) for result in results}),
        "results_file": str(output_path.relative_to(root)),
        "manual_review_pending": True,
    }
    summary_path = output_path.with_suffix(".summary.json")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
