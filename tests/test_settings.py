from pathlib import Path

from graphrag.config.load_config import load_config
import yaml


EXPECTED_TYPES = {
    "ATTACK_TECHNIQUE",
    "DEFENSE_CONTROL",
    "COMPONENT",
    "VULNERABILITY",
    "TOOL",
    "STANDARD",
    "EVALUATION",
}


def test_settings_pin_models_domain_prompt_and_entity_types() -> None:
    settings = yaml.safe_load(Path("settings.yaml").read_text(encoding="utf-8"))
    extract_graph = settings["extract_graph"]
    completion = settings["completion_models"]["default_completion_model"]
    embedding = settings["embedding_models"]["default_embedding_model"]

    assert extract_graph["prompt"] == "prompts/extract_graph.txt"
    assert set(extract_graph["entity_types"]) == EXPECTED_TYPES
    assert extract_graph["max_gleanings"] == 0
    assert settings["extract_claims"]["enabled"] is False
    assert completion["type"] == "glm_json_object"
    assert completion["model"] == "${ZAI_CHAT_MODEL}"
    assert completion["api_key"] == "${ZAI_API_KEY}"
    assert completion["api_base"] == "${ZHIPU_API_BASE}"
    assert completion["call_args"] == {
        "extra_body": {"thinking": {"type": "disabled"}}
    }
    assert embedding["model"] == "${ZHIPU_EMBEDDING_MODEL}"
    assert embedding["api_key"] == "${ZHIPU_API_KEY}"
    assert embedding["api_base"] == "${ZHIPU_API_BASE}"
    assert embedding["call_args"]["dimensions"] == "${ZHIPU_EMBEDDING_DIMENSIONS}"
    assert completion["rate_limit"] == {
        "type": "sliding_window",
        "period_in_seconds": 10,
        "requests_per_period": 20,
    }
    assert settings["cache"]["storage"]["base_dir"] == (
        "cache/glm-4.5-air-summary-20260713-v1"
    )
    assert settings["vector_store"]["vector_size"] == "${ZHIPU_EMBEDDING_DIMENSIONS}"


def test_active_prompts_are_not_raw_tuned_outputs() -> None:
    settings = yaml.safe_load(Path("settings.yaml").read_text(encoding="utf-8"))
    prompt_paths = [
        settings["extract_graph"]["prompt"],
        settings["summarize_descriptions"]["prompt"],
        settings["community_reports"]["graph_prompt"],
        settings["community_reports"]["text_prompt"],
    ]

    assert all("prompts/tuned" not in path for path in prompt_paths)
    assert all(Path(path).is_file() for path in prompt_paths)


def test_settings_isolate_summary_only_input() -> None:
    settings = yaml.safe_load(Path("settings.yaml").read_text(encoding="utf-8"))

    assert settings["input_storage"]["base_dir"] == "summary_input"
    assert settings["input"] == {
        "type": "json",
        "file_pattern": ".*summary_corpus\\.json$$",
        "encoding": "utf-8",
        "id_column": "id",
        "title_column": "title",
        "text_column": "text",
    }
    assert settings["chunking"]["prepend_metadata"] == []


def test_graphrag_can_interpolate_summary_file_pattern(monkeypatch) -> None:
    environment = {
        "ZAI_API_KEY": "test-zai-key",
        "ZAI_CHAT_MODEL": "glm-4.5-air",
        "ZHIPU_API_KEY": "test-embedding-key",
        "ZHIPU_API_BASE": "https://example.test/v4",
        "ZHIPU_EMBEDDING_MODEL": "embedding-3",
        "ZHIPU_EMBEDDING_DIMENSIONS": "2048",
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    config = load_config(Path("."))

    assert config.input.file_pattern == ".*summary_corpus\\.json$"
