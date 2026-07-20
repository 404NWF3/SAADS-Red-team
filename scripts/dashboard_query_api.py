"""Small, local-only HTTP API for running approved GraphRAG query modes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


METHODS = ("basic", "local", "global", "drift")
MAX_BODY_BYTES = 32 * 1024
MAX_QUESTION_LENGTH = 2_000
ROOT = Path(__file__).resolve().parents[1]
QUERY_ROOT = Path(os.getenv("GRAPHRAG_ROOT", str(ROOT))).resolve()
QUERY_LOCK = threading.Lock()
SECRET_PATTERN = re.compile(r"(?i)(?:sk|key|token)[-_a-z0-9]{8,}")


class RequestError(ValueError):
    """An invalid query request with an HTTP status attached."""

    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


def validate_payload(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        raise RequestError("请求体必须是 JSON 对象。")

    method = payload.get("method")
    question = payload.get("question")
    if method not in METHODS:
        raise RequestError(f"查询模式必须是：{', '.join(METHODS)}。")
    if not isinstance(question, str):
        raise RequestError("question 必须是字符串。")

    question = question.strip()
    if not question:
        raise RequestError("请输入查询问题。")
    if len(question) > MAX_QUESTION_LENGTH:
        raise RequestError(f"问题不能超过 {MAX_QUESTION_LENGTH} 个字符。")
    return method, question


def build_query_command(method: str, question: str) -> list[str]:
    return [
        sys.executable,
        "scripts/graphrag_cli.py",
        "query",
        "--root",
        str(QUERY_ROOT),
        "--method",
        method,
        "--response-type",
        "Multiple Paragraphs with source citations",
        question,
    ]


def prepare_query_root() -> None:
    """Create a writable GraphRAG root backed by links to immutable app data."""
    if QUERY_ROOT == ROOT:
        return
    QUERY_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ("settings.yaml", ".env", "prompts", "output", "cache", "logs"):
        source = ROOT / name
        target = QUERY_ROOT / name
        if not source.exists() or target.exists():
            continue
        target.symlink_to(source, target_is_directory=source.is_dir())


def safe_error_text(value: str) -> str:
    redacted = SECRET_PATTERN.sub("[REDACTED]", normalize_output_encoding(value.strip()))
    return redacted[-4_000:] if redacted else "GraphRAG 查询执行失败。"


def encoding_damage_score(value: str) -> int:
    controls = sum("\u0080" <= character <= "\u009f" for character in value)
    markers = sum(value.count(marker) for marker in ("Ã", "Â", "â", "å", "æ", "ç"))
    return controls * 4 + markers


def normalize_output_encoding(value: str) -> str:
    """Repair the reversible UTF-8-as-Latin-1 output seen in the Linux CLI."""
    try:
        candidate = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    return candidate if encoding_damage_score(candidate) < encoding_damage_score(value) else value


def run_query(method: str, question: str) -> dict[str, Any]:
    timeout = int(os.getenv("GRAPHRAG_QUERY_TIMEOUT_SECONDS", "600"))
    command = build_query_command(method, question)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RequestError(
            f"查询超过 {timeout} 秒，已停止执行。",
            HTTPStatus.GATEWAY_TIMEOUT,
        ) from error

    elapsed = round(time.perf_counter() - started, 3)
    if completed.returncode != 0:
        raise RequestError(
            safe_error_text(completed.stderr),
            HTTPStatus.BAD_GATEWAY,
        )
    answer = normalize_output_encoding(completed.stdout.strip())
    if not answer:
        raise RequestError("GraphRAG 未返回内容。", HTTPStatus.BAD_GATEWAY)
    return {
        "ok": True,
        "method": method,
        "question": question,
        "answer": answer,
        "elapsedSeconds": elapsed,
    }


class QueryHandler(BaseHTTPRequestHandler):
    server_version = "GraphRAGQuery/1.0"

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}", flush=True)

    def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "未找到接口。"})
            return
        self.send_json(
            HTTPStatus.OK,
            {"ok": True, "status": "ready", "busy": QUERY_LOCK.locked()},
        )

    def do_POST(self) -> None:
        if self.path != "/query":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "未找到接口。"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_BODY_BYTES:
                raise RequestError("请求体为空或过大。", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            method, question = validate_payload(payload)
        except json.JSONDecodeError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "请求体不是有效 JSON。"})
            return
        except (UnicodeDecodeError, ValueError) as error:
            status = error.status if isinstance(error, RequestError) else HTTPStatus.BAD_REQUEST
            self.send_json(status, {"ok": False, "error": str(error)})
            return

        if not QUERY_LOCK.acquire(blocking=False):
            self.send_json(
                HTTPStatus.CONFLICT,
                {"ok": False, "error": "已有 GraphRAG 查询正在运行，请稍后再试。"},
            )
            return
        try:
            result = run_query(method, question)
            self.send_json(HTTPStatus.OK, result)
        except RequestError as error:
            self.send_json(error.status, {"ok": False, "error": str(error)})
        finally:
            QUERY_LOCK.release()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the local GraphRAG query API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prepare_query_root()
    server = ThreadingHTTPServer((args.host, args.port), QueryHandler)
    print(f"GraphRAG query API listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
