from pydantic import BaseModel

from llm_defense_graphrag.deepseek_completion import adapt_response_format


class ExampleReport(BaseModel):
    title: str


def test_pydantic_response_format_uses_json_object_api_mode() -> None:
    arguments = {"response_format": ExampleReport, "temperature": 0}

    assert adapt_response_format(arguments) == {
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    assert arguments["response_format"] is ExampleReport


def test_unstructured_completion_arguments_are_unchanged() -> None:
    arguments = {"response_format": None, "temperature": 0}

    assert adapt_response_format(arguments) == arguments
