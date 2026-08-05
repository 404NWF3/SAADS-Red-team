"""Probe and optionally load the project GraphRAG index for grill assessments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from saads_attack_agent.security_graph import REQUIRED_TABLES, SecurityGraph


@dataclass(frozen=True)
class GraphRuntime:
    enabled: bool
    skipped_reason: str | None  # None | disabled_by_config | index_unavailable | index_load_failed
    graph: SecurityGraph | None


def probe_graph_index(root: Path) -> bool:
    if not (root / "settings.yaml").is_file():
        return False
    output_dir = root / "output"
    return all((output_dir / f"{table}.parquet").is_file() for table in REQUIRED_TABLES)


def resolve_graph_runtime(*, root: Path, use_graphrag: bool) -> GraphRuntime:
    if not use_graphrag:
        return GraphRuntime(
            enabled=False,
            skipped_reason="disabled_by_config",
            graph=None,
        )
    if not probe_graph_index(root):
        return GraphRuntime(
            enabled=False,
            skipped_reason="index_unavailable",
            graph=None,
        )
    try:
        graph = SecurityGraph.load(root)
    except Exception:
        return GraphRuntime(
            enabled=False,
            skipped_reason="index_load_failed",
            graph=None,
        )
    return GraphRuntime(enabled=True, skipped_reason=None, graph=graph)
