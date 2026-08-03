"""GraphRAG completion adapter for GLM structured responses."""

from __future__ import annotations

from typing import Any

from graphrag_llm.completion import register_completion
from graphrag_llm.completion.completion_factory import completion_factory
from pydantic import BaseModel, ValidationError

from llm_defense_graphrag.deepseek_completion import (
    DeepSeekJsonObjectCompletion,
    adapt_response_format,
)


COMPLETION_TYPE = "glm_json_object"


def add_schema_retry_message(
    messages: object,
    response_format: type[BaseModel],
) -> list[Any]:
    """Add a corrective turn and therefore a distinct cache key."""
    original = (
        [{"role": "user", "content": messages}]
        if isinstance(messages, str)
        else list(messages)  # type: ignore[arg-type]
    )
    required_fields = ", ".join(response_format.model_fields)
    return [
        *original,
        {
            "role": "user",
            "content": (
                "The previous response did not match the required JSON object. "
                f"Return only these exact fields now: {required_fields}."
            ),
        },
    ]


class GlmJsonObjectCompletion(DeepSeekJsonObjectCompletion):
    """Retry once when GLM returns valid JSON with the wrong local schema."""

    async def completion_async(self, /, **kwargs: Any) -> Any:
        try:
            return await super().completion_async(**kwargs)
        except ValidationError:
            response_format = kwargs.get("response_format")
            if not (
                isinstance(response_format, type)
                and issubclass(response_format, BaseModel)
            ):
                raise
            retried = dict(kwargs)
            retried["messages"] = add_schema_retry_message(
                kwargs.get("messages", []),
                response_format,
            )
            return await super().completion_async(**retried)


def register_glm_completion() -> None:
    """Register JSON Object transport while retaining local schema validation."""
    if COMPLETION_TYPE not in completion_factory:
        register_completion(
            completion_type=COMPLETION_TYPE,
            completion_initializer=GlmJsonObjectCompletion,
            scope="singleton",
        )


__all__ = [
    "COMPLETION_TYPE",
    "GlmJsonObjectCompletion",
    "add_schema_retry_message",
    "adapt_response_format",
    "register_glm_completion",
]
