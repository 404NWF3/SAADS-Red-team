from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.workflows.extract_graph import (
    run_workflow as stock_extract_graph_workflow,
)
from graphrag.index.workflows.factory import PipelineFactory
from graphrag_llm.completion import create_completion

from llm_defense_graphrag.entity_alignment import (
    GlmAmbiguityResolver,
    align_graph_tables,
    load_entity_registry,
)

if TYPE_CHECKING:
    from graphrag.config.models.graph_rag_config import GraphRagConfig
    from graphrag.index.typing.context import PipelineRunContext


ENTITY_REGISTRY_PATH = Path("config/entity_aliases.yaml")


async def run_extract_graph_with_alignment(
    config: "GraphRagConfig",
    context: "PipelineRunContext",
) -> WorkflowFunctionOutput:
    stock_output = await stock_extract_graph_workflow(config, context)
    entities = await context.output_table_provider.read_dataframe("entities")
    relationships = await context.output_table_provider.read_dataframe(
        "relationships"
    )

    model_config = config.get_completion_model_config(
        config.extract_graph.completion_model_id
    )
    completion = create_completion(
        model_config,
        cache=context.cache.child("entity_alignment"),
        cache_key_creator=cache_key_creator,
    )
    alignment = await align_graph_tables(
        entities,
        relationships,
        load_entity_registry(ENTITY_REGISTRY_PATH),
        resolver=GlmAmbiguityResolver(completion),
    )
    await context.output_table_provider.write_dataframe(
        "entities", alignment.entities
    )
    await context.output_table_provider.write_dataframe(
        "relationships", alignment.relationships
    )
    await context.output_table_provider.write_dataframe(
        "entity_alignment", alignment.audit
    )

    return WorkflowFunctionOutput(
        result={
            "entities": alignment.entities,
            "relationships": alignment.relationships,
            "entity_alignment": alignment.audit,
        },
        stop=stock_output.stop,
    )


def register_project_workflows() -> None:
    PipelineFactory.register(
        "extract_graph",
        run_extract_graph_with_alignment,
    )
