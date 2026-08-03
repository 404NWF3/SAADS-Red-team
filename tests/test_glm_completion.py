from pydantic import BaseModel

from llm_defense_graphrag.glm_completion import (
    COMPLETION_TYPE,
    add_schema_retry_message,
    adapt_response_format,
)


class ExampleAlignment(BaseModel):
    canonical_title: str


def test_glm_adapter_preserves_local_schema_but_requests_json_object() -> None:
    arguments = {
        "response_format": ExampleAlignment,
        "temperature": 0,
    }

    assert COMPLETION_TYPE == "glm_json_object"
    assert adapt_response_format(arguments) == {
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    assert arguments["response_format"] is ExampleAlignment


def test_glm_schema_retry_message_changes_cache_key_and_names_required_fields() -> None:
    messages = [{"role": "user", "content": "Create the report."}]

    retried = add_schema_retry_message(messages, ExampleAlignment)

    assert retried[:-1] == messages
    assert retried is not messages
    assert retried[-1]["role"] == "user"
    assert "canonical_title" in retried[-1]["content"]
    assert messages == [{"role": "user", "content": "Create the report."}]
