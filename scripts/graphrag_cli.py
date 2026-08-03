"""Project GraphRAG CLI with summary-only entity alignment registered."""

from graphrag.cli.main import app

from llm_defense_graphrag.glm_completion import register_glm_completion
from llm_defense_graphrag.graphrag_workflows import register_project_workflows


if __name__ == "__main__":
    register_glm_completion()
    register_project_workflows()
    app()
