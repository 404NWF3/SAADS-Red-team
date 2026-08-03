import asyncio
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from graphrag.index.typing.workflow import WorkflowFunctionOutput

from llm_defense_graphrag.graphrag_workflows import (
    run_extract_graph_with_alignment,
)


def test_alignment_workflow_rewrites_tables_before_downstream_steps(
    monkeypatch,
) -> None:
    class FakeTableProvider:
        def __init__(self) -> None:
            self.tables = {
                "entities": pd.DataFrame(
                    [
                        {
                            "title": "HUGGINGFACE",
                            "type": "COMPONENT",
                            "description": "Model hosting platform.",
                            "text_unit_ids": ["u1"],
                            "frequency": 1,
                        },
                        {
                            "title": "HUGGING FACE",
                            "type": "COMPONENT",
                            "description": "AI platform.",
                            "text_unit_ids": ["u2"],
                            "frequency": 1,
                        },
                    ]
                ),
                "relationships": pd.DataFrame(
                    columns=[
                        "source",
                        "target",
                        "description",
                        "text_unit_ids",
                        "weight",
                    ]
                ),
            }

        async def read_dataframe(self, name: str) -> pd.DataFrame:
            return self.tables[name].copy()

        async def write_dataframe(self, name: str, frame: pd.DataFrame) -> None:
            self.tables[name] = frame.copy()

    class FakeCache:
        def child(self, name: str) -> "FakeCache":
            assert name == "entity_alignment"
            return self

    async def fake_stock_workflow(_config, _context) -> WorkflowFunctionOutput:
        return WorkflowFunctionOutput(result={"stock": True})

    provider = FakeTableProvider()
    context = SimpleNamespace(
        output_table_provider=provider,
        cache=FakeCache(),
    )
    config = SimpleNamespace(
        extract_graph=SimpleNamespace(completion_model_id="default_completion_model"),
        get_completion_model_config=lambda _model_id: object(),
    )

    monkeypatch.setattr(
        "llm_defense_graphrag.graphrag_workflows.stock_extract_graph_workflow",
        fake_stock_workflow,
    )
    monkeypatch.setattr(
        "llm_defense_graphrag.graphrag_workflows.create_completion",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        "llm_defense_graphrag.graphrag_workflows.ENTITY_REGISTRY_PATH",
        Path("config/entity_aliases.yaml"),
    )

    output = asyncio.run(run_extract_graph_with_alignment(config, context))

    assert output.stop is False
    assert provider.tables["entities"]["title"].tolist() == ["HUGGING FACE"]
    assert provider.tables["entities"].iloc[0]["frequency"] == 2
    assert provider.tables["relationships"].empty
    assert provider.tables["entity_alignment"]["source_title"].tolist() == [
        "HUGGINGFACE",
        "HUGGING FACE",
    ]
