from __future__ import annotations

from pathlib import Path

import pytest

from saads_grill_agent.graph_runtime import probe_graph_index, resolve_graph_runtime


def test_probe_false_when_missing(tmp_path: Path) -> None:
    assert probe_graph_index(tmp_path) is False


def test_probe_true_when_settings_and_tables_exist(tmp_path: Path) -> None:
    (tmp_path / "settings.yaml").write_text("x: 1\n", encoding="utf-8")
    out = tmp_path / "output"
    out.mkdir()
    for name in (
        "entities",
        "communities",
        "community_reports",
        "text_units",
        "relationships",
    ):
        (out / f"{name}.parquet").write_bytes(b"x")
    assert probe_graph_index(tmp_path) is True


def test_resolve_disabled_by_config(tmp_path: Path) -> None:
    rt = resolve_graph_runtime(root=tmp_path, use_graphrag=False)
    assert rt.enabled is False
    assert rt.skipped_reason == "disabled_by_config"
    assert rt.graph is None


def test_resolve_index_unavailable(tmp_path: Path) -> None:
    rt = resolve_graph_runtime(root=tmp_path, use_graphrag=True)
    assert rt.enabled is False
    assert rt.skipped_reason == "index_unavailable"
    assert rt.graph is None


def test_resolve_load_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "settings.yaml").write_text("x: 1\n", encoding="utf-8")
    out = tmp_path / "output"
    out.mkdir()
    for name in (
        "entities",
        "communities",
        "community_reports",
        "text_units",
        "relationships",
    ):
        (out / f"{name}.parquet").write_bytes(b"x")

    def _raise(_root: Path) -> None:
        raise RuntimeError("load failed")

    monkeypatch.setattr(
        "saads_grill_agent.graph_runtime.SecurityGraph.load",
        _raise,
    )

    rt = resolve_graph_runtime(root=tmp_path, use_graphrag=True)
    assert rt.enabled is False
    assert rt.skipped_reason == "index_load_failed"
    assert rt.graph is None
