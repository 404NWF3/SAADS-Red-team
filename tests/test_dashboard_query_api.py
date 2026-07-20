import pytest

from scripts.dashboard_query_api import (
    RequestError,
    build_query_command,
    normalize_output_encoding,
    validate_payload,
)


def test_validate_payload_accepts_supported_query() -> None:
    assert validate_payload({"method": "local", "question": "  提示注入如何缓解？  "}) == (
        "local",
        "提示注入如何缓解？",
    )


@pytest.mark.parametrize("method", ["shell", "", None])
def test_validate_payload_rejects_unapproved_method(method: object) -> None:
    with pytest.raises(RequestError):
        validate_payload({"method": method, "question": "test"})


@pytest.mark.parametrize("question", ["", "   ", None, "x" * 2_001])
def test_validate_payload_rejects_invalid_question(question: object) -> None:
    with pytest.raises(RequestError):
        validate_payload({"method": "basic", "question": question})


def test_query_command_is_an_argument_list() -> None:
    command = build_query_command("basic", "question; echo unsafe")
    assert command[-1] == "question; echo unsafe"
    assert command[1:4] == ["scripts/graphrag_cli.py", "query", "--root"]
    assert "--method" in command


def test_normalize_output_encoding_repairs_utf8_mojibake() -> None:
    damaged = "提示注入与两项防御措施".encode("utf-8").decode("latin-1")
    assert normalize_output_encoding(damaged) == "提示注入与两项防御措施"


def test_normalize_output_encoding_preserves_valid_unicode() -> None:
    assert normalize_output_encoding("提示注入 — defense") == "提示注入 — defense"
