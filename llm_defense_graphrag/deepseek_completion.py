"""GraphRAG completion adapter for DeepSeek structured responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from graphrag_llm.completion import register_completion
from graphrag_llm.completion.completion_factory import completion_factory
from graphrag_llm.completion.lite_llm_completion import LiteLLMCompletion


COMPLETION_TYPE = "deepseek_json_object"


def adapt_response_format(arguments: dict[str, Any]) -> dict[str, Any]:
    """Map Pydantic JSON Schema requests to DeepSeek's JSON Object mode."""
    adapted = dict(arguments)
    response_format = adapted.get("response_format")
    if (
        isinstance(response_format, type)
        and issubclass(response_format, BaseModel)
    ):
        adapted["response_format"] = {"type": "json_object"}
    return adapted


class DeepSeekJsonObjectCompletion(LiteLLMCompletion):
    """Keep GraphRAG's local Pydantic validation while using JSON Object mode."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        completion = self._completion
        completion_async = self._completion_async

        def compatible_completion(**arguments: Any):
            return completion(**adapt_response_format(arguments))

        async def compatible_completion_async(**arguments: Any):
            return await completion_async(**adapt_response_format(arguments))

        self._completion = compatible_completion
        self._completion_async = compatible_completion_async


def register_deepseek_completion() -> None:
    """Register the adapter once before GraphRAG loads the project settings."""
    if COMPLETION_TYPE not in completion_factory:
        register_completion(
            completion_type=COMPLETION_TYPE,
            completion_initializer=DeepSeekJsonObjectCompletion,
            scope="singleton",
        )
