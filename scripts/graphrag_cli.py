"""Project GraphRAG CLI with the DeepSeek compatibility provider registered."""

from graphrag.cli.main import app

from llm_defense_graphrag.deepseek_completion import register_deepseek_completion


if __name__ == "__main__":
    register_deepseek_completion()
    app()
