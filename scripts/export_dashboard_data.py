from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


RELATION_TERMS = {
    "mitigates": ("mitigat", "prevent", "protect", "缓解", "防止", "保护"),
    "exploits": ("exploit", "利用"),
    "targets": ("target", "针对"),
    "detects": ("detect", "monitor", "检测", "监测"),
    "evaluates": ("evaluat", "assess", "test", "评估", "测试"),
    "implements": ("implement", "enforce", "实施", "执行"),
    "recommends": ("recommend", "require", "建议", "要求"),
}


def primary_semantic(description: object) -> str:
    lowered = str(description).lower()
    for label, terms in RELATION_TERMS.items():
        if any(term in lowered for term in terms):
            return label
    return "other"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_query_history(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        records.append(
            {
                "id": record["id"],
                "method": record["method"],
                "question": record["question"],
                "answer": record["answer"],
                "elapsedSeconds": record["elapsed_seconds"],
                "success": record["returncode"] == 0,
            }
        )
    return records


def build_payload(root: Path) -> dict[str, object]:
    output = root / "output"
    reports = root / "reports"
    build = load_json(reports / "build_summary.json")
    quality = load_json(reports / "graph_quality.json")
    corpus = load_json(reports / "corpus_summary.json")
    evaluation = load_json(reports / "query_evaluation.summary.json")
    entities = pd.read_parquet(output / "entities.parquet")
    relationships = pd.read_parquet(output / "relationships.parquet")
    community_reports = pd.read_parquet(output / "community_reports.parquet")

    nodes: list[list[object]] = []
    node_index: dict[str, int] = {}
    for row in entities[["title", "type", "degree"]].itertuples(index=False):
        title = str(row.title)
        node_index[title] = len(nodes)
        nodes.append([title, str(row.type), int(row.degree)])

    edges: list[list[object]] = []
    for row in relationships[["source", "target", "description", "weight"]].itertuples(index=False):
        source = node_index.get(str(row.source))
        target = node_index.get(str(row.target))
        if source is None or target is None:
            continue
        edges.append(
            [source, target, primary_semantic(row.description), round(float(row.weight), 2)]
        )

    top_communities = []
    for row in community_reports.sort_values(
        ["rank", "size"], ascending=[False, False]
    ).head(20).itertuples(index=False):
        top_communities.append(
            {
                "id": int(row.community),
                "rank": round(float(row.rank), 1),
                "size": int(row.size),
                "title": str(row.title),
                "summary": str(row.summary),
            }
        )

    coverage = quality["attack_defense_path_coverage"]
    degree = quality["degree"]
    return {
        "generatedAt": build["finished_at"],
        "models": build["models"],
        "elapsedSeconds": build["elapsed_seconds"],
        "artifacts": quality["artifacts"],
        "entityTypes": quality["entity_types"],
        "relationshipSemantics": quality["relationship_semantics"],
        "sources": corpus["sources"],
        "sourceTypes": corpus["source_types"],
        "securityDomains": corpus["security_domains"],
        "quality": {
            "attackCount": coverage["attack_count"],
            "coveredCount": coverage["covered_count"],
            "coverageRatio": coverage["coverage_ratio"],
            "uncoveredCount": coverage["attack_count"] - coverage["covered_count"],
            "isolatedCount": degree["isolated_count"],
            "isolatedRatio": degree["isolated_ratio"],
            "degreeMedian": degree["median"],
            "degreeP95": degree["p95"],
            "degreeMaximum": degree["maximum"],
            "duplicateCandidates": len(quality["duplicate_or_synonym_candidates"]),
            "offSchemaEntities": sum(
                int(quality["entity_types"]["counts"].get(kind, 0))
                for kind in quality["entity_types"]["unknown"]
            ),
        },
        "evaluation": evaluation,
        "queryHistory": load_query_history(reports / "query_evaluation.jsonl"),
        "topCommunities": top_communities,
        "nodes": nodes,
        "edges": edges,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export static GraphRAG dashboard data.")
    parser.add_argument(
        "destination",
        type=Path,
        default=Path("dashboard/app/data/graphrag.json"),
        nargs="?",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    payload = build_payload(args.root.resolve())
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "destination": str(args.destination.resolve()),
                "bytes": args.destination.stat().st_size,
                "nodes": len(payload["nodes"]),
                "edges": len(payload["edges"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
