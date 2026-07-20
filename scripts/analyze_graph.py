from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_TYPES = {
    "ATTACK_TECHNIQUE",
    "DEFENSE_CONTROL",
    "COMPONENT",
    "VULNERABILITY",
    "TOOL",
    "STANDARD",
    "EVALUATION",
}
SEMANTIC_TERMS = {
    "mitigates": ("mitigat", "prevent", "protect", "缓解", "防止", "保护"),
    "exploits": ("exploit", "利用"),
    "targets": ("target", "针对"),
    "detects": ("detect", "monitor", "检测", "监测"),
    "evaluates": ("evaluat", "assess", "test", "评估", "测试"),
    "implements": ("implement", "enforce", "实施", "执行"),
    "recommends": ("recommend", "require", "建议", "要求"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze GraphRAG parquet quality.")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser.parse_args()


def read_required(output_dir: Path, name: str) -> pd.DataFrame:
    path = output_dir / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing GraphRAG artifact: {path}")
    return pd.read_parquet(path)


def canonical_title(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value).upper())


def native(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def degree_stats(entities: pd.DataFrame, relationships: pd.DataFrame) -> dict[str, Any]:
    degree: Counter[str] = Counter()
    for row in relationships[["source", "target"]].itertuples(index=False):
        degree[str(row.source)] += 1
        degree[str(row.target)] += 1
    titles = entities["title"].astype(str).tolist()
    values = pd.Series([degree[title] for title in titles], dtype="int64")
    isolated = [title for title in titles if degree[title] == 0]
    return {
        "minimum": int(values.min()) if len(values) else 0,
        "median": float(values.median()) if len(values) else 0.0,
        "p95": float(values.quantile(0.95)) if len(values) else 0.0,
        "maximum": int(values.max()) if len(values) else 0,
        "isolated_count": len(isolated),
        "isolated_ratio": round(len(isolated) / len(titles), 4) if titles else 0.0,
        "isolated_sample": isolated[:25],
    }


def duplicate_candidates(entities: pd.DataFrame) -> list[dict[str, Any]]:
    groups: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    for row in entities[["title", "type"]].itertuples(index=False):
        groups[(str(row.type), canonical_title(row.title))].append(str(row.title))
    return [
        {"type": key[0], "canonical": key[1], "titles": sorted(set(titles))}
        for key, titles in groups.items()
        if len(set(titles)) > 1
    ][:100]


def relationship_quality(
    entities: pd.DataFrame, relationships: pd.DataFrame
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    type_by_title = dict(zip(entities["title"].astype(str), entities["type"].astype(str)))
    semantics: Counter[str] = Counter()
    anomalies: list[dict[str, Any]] = []
    for row in relationships.itertuples(index=False):
        description = str(getattr(row, "description", ""))
        lowered = description.lower()
        labels = [name for name, terms in SEMANTIC_TERMS.items() if any(term in lowered for term in terms)]
        semantics.update(labels or ["other"])
        source = str(row.source)
        target = str(row.target)
        source_type = type_by_title.get(source)
        target_type = type_by_title.get(target)
        wrong_mitigation_direction = (
            "mitigates" in labels
            and source_type == "ATTACK_TECHNIQUE"
            and target_type == "DEFENSE_CONTROL"
        )
        wrong_attack_direction = (
            ("exploits" in labels or "targets" in labels)
            and source_type == "DEFENSE_CONTROL"
            and target_type in {"ATTACK_TECHNIQUE", "VULNERABILITY"}
        )
        if wrong_mitigation_direction or wrong_attack_direction:
            anomalies.append(
                {
                    "source": source,
                    "source_type": source_type,
                    "target": target,
                    "target_type": target_type,
                    "description": description,
                }
            )
    return dict(semantics.most_common()), anomalies[:50]


def attack_defense_coverage(
    entities: pd.DataFrame, relationships: pd.DataFrame, max_hops: int = 2
) -> dict[str, Any]:
    type_by_title = dict(zip(entities["title"].astype(str), entities["type"].astype(str)))
    graph: defaultdict[str, set[str]] = defaultdict(set)
    for row in relationships[["source", "target"]].itertuples(index=False):
        source, target = str(row.source), str(row.target)
        graph[source].add(target)
        graph[target].add(source)
    attacks = sorted(title for title, kind in type_by_title.items() if kind == "ATTACK_TECHNIQUE")
    covered: list[str] = []
    uncovered: list[str] = []
    for attack in attacks:
        queue = deque([(attack, 0)])
        seen = {attack}
        found = False
        while queue and not found:
            node, hops = queue.popleft()
            if hops and type_by_title.get(node) == "DEFENSE_CONTROL":
                found = True
                break
            if hops == max_hops:
                continue
            for neighbor in graph[node] - seen:
                seen.add(neighbor)
                queue.append((neighbor, hops + 1))
        (covered if found else uncovered).append(attack)
    return {
        "max_hops": max_hops,
        "attack_count": len(attacks),
        "covered_count": len(covered),
        "coverage_ratio": round(len(covered) / len(attacks), 4) if attacks else 0.0,
        "uncovered_sample": uncovered[:50],
    }


def community_quality(reports: pd.DataFrame) -> dict[str, Any]:
    title_column = "title" if "title" in reports else None
    content_column = "full_content" if "full_content" in reports else "summary"
    missing_title = int(reports[title_column].isna().sum()) if title_column else len(reports)
    missing_content = int(reports[content_column].fillna("").astype(str).str.strip().eq("").sum())
    rank_column = "rank" if "rank" in reports else None
    ordered = reports.sort_values(rank_column, ascending=False) if rank_column else reports
    sample_columns = [column for column in ("community", "title", "summary", "rank") if column in reports]
    sample = [
        {key: native(value) for key, value in row.items()}
        for row in ordered[sample_columns].head(20).to_dict(orient="records")
    ]
    return {
        "report_count": len(reports),
        "missing_title_count": missing_title,
        "missing_content_count": missing_content,
        "top_reports": sample,
    }


def build_report(output_dir: Path) -> dict[str, Any]:
    entities = read_required(output_dir, "entities")
    relationships = read_required(output_dir, "relationships")
    communities = read_required(output_dir, "communities")
    reports = read_required(output_dir, "community_reports")
    documents = read_required(output_dir, "documents")
    text_units = read_required(output_dir, "text_units")

    type_counts = entities["type"].fillna("UNKNOWN").astype(str).value_counts().to_dict()
    semantics, anomalies = relationship_quality(entities, relationships)
    return {
        "artifacts": {
            "documents": len(documents),
            "text_units": len(text_units),
            "entities": len(entities),
            "relationships": len(relationships),
            "communities": len(communities),
            "community_reports": len(reports),
        },
        "entity_types": {
            "counts": type_counts,
            "expected": sorted(EXPECTED_TYPES),
            "unknown": sorted(set(type_counts) - EXPECTED_TYPES),
        },
        "duplicate_or_synonym_candidates": duplicate_candidates(entities),
        "relationship_semantics": semantics,
        "relationship_direction_anomalies": anomalies,
        "degree": degree_stats(entities, relationships),
        "communities": community_quality(reports),
        "attack_defense_path_coverage": attack_defense_coverage(entities, relationships),
    }


def render_markdown(report: dict[str, Any]) -> str:
    artifacts = report["artifacts"]
    types = report["entity_types"]
    degree = report["degree"]
    coverage = report["attack_defense_path_coverage"]
    communities = report["communities"]
    lines = [
        "# GraphRAG 图谱质量报告",
        "",
        "## 产物规模",
        "",
        *[f"- {name}: {count}" for name, count in artifacts.items()],
        "",
        "## 实体类型",
        "",
        *[f"- {name}: {count}" for name, count in types["counts"].items()],
        f"- 越界类型: {', '.join(types['unknown']) if types['unknown'] else '无'}",
        "",
        "## 关系与连通性",
        "",
        f"- 关系语义分布: {json.dumps(report['relationship_semantics'], ensure_ascii=False)}",
        f"- 方向异常候选: {len(report['relationship_direction_anomalies'])}",
        f"- 孤立节点: {degree['isolated_count']} ({degree['isolated_ratio']:.2%})",
        f"- 节点度：min={degree['minimum']}, median={degree['median']}, p95={degree['p95']}, max={degree['maximum']}",
        f"- 攻击—防御两跳覆盖: {coverage['covered_count']}/{coverage['attack_count']} ({coverage['coverage_ratio']:.2%})",
        "",
        "## 社区报告",
        "",
        f"- 报告数: {communities['report_count']}",
        f"- 缺少标题: {communities['missing_title_count']}",
        f"- 缺少正文: {communities['missing_content_count']}",
        "",
        "详细候选与样本见 `reports/graph_quality.json`。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    report = build_report(args.output_dir)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    (args.reports_dir / "graph_quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.reports_dir / "graph_quality.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(json.dumps(report["artifacts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
