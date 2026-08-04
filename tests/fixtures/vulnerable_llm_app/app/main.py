"""Minimal FastAPI surface for the vulnerable fixture."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.debug import assembled_system_prompt_for_debug
from app.rag import build_model_input
from app.tools import ToolCall, run_model_selected_tool, write_file_tool

app = FastAPI(title="vulnerable-llm-app")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ToolRequest(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict = Field(default_factory=dict)


class WriteRequest(BaseModel):
    path: str
    content: str
    human_approved: bool = False


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    return {"model_input": build_model_input(request.message)}


@app.get("/debug/system-prompt")
def debug_system_prompt(query: str = "status") -> dict[str, str]:
    """Debug endpoint returns the assembled system prompt."""
    return {"system_prompt": assembled_system_prompt_for_debug(query)}


@app.post("/tools/run")
def tools_run(request: ToolRequest) -> dict[str, str]:
    result = run_model_selected_tool(
        ToolCall(name=request.name, arguments=request.arguments)
    )
    return {"result": result}


@app.post("/tools/write-file")
def tools_write_file(request: WriteRequest) -> dict[str, str]:
    result = write_file_tool(
        {"path": request.path, "content": request.content},
        human_approved=request.human_approved,
    )
    return {"result": result}
