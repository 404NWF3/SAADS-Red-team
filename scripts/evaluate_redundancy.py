from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_PARQUET = ("entities.parquet", "relationships.parquet")
DEFAULT_COSINE_THRESHOLD = 0.85
ENTITY_EMBEDDING_TABLE = "entity_description"


@dataclass
class UnionFind:
    parent: list[int]

    @classmethod
    def create(cls, size: int) -> UnionFind:
        return cls(parent=list(range(size)))

    def find(self, item: int) -> int:
        parent = self.parent
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Entity/Relation Redundancy Rate evaluation over GraphRAG output."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="GraphRAG output directory. Defaults to <root>/output.",
    )
    parser.add_argument(
        "--zip",
        type=Path,
        default=None,
        help="Optional output.zip. Used only when required parquet files are missing.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Report output directory. Defaults to <root>/reports.",
    )
    parser.add_argument(
        "--cosine-threshold",
        type=float,
        default=DEFAULT_COSINE_THRESHOLD,
        help=(
            "Minimum cosine similarity for same-type embedding clusters "
            f"(default: {DEFAULT_COSINE_THRESHOLD})."
        ),
    )
    parser.add_argument(
        "--cluster-sample-limit",
        type=int,
        default=50,
        help="Max multi-member clusters to include in the JSON report.",
    )
    return parser.parse_args()


def canonical_title(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value).upper())


def ensure_output_dir(root: Path, output_dir: Path, zip_path: Path | None) -> Path:
    missing = [name for name in REQUIRED_PARQUET if not (output_dir / name).exists()]
    if not missing:
        return output_dir.resolve()

    candidate = zip_path if zip_path is not None else root / "output.zip"
    if not candidate.exists():
        raise FileNotFoundError(
            f"Missing {missing} under {output_dir} and zip not found at {candidate}"
        )

    extract_dir = (root / "reports" / ".cache" / "output_from_zip").resolve()
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(candidate) as archive:
        archive.extractall(extract_dir)

    nested = extract_dir / "output"
    resolved = nested if nested.is_dir() else extract_dir
    still_missing = [name for name in REQUIRED_PARQUET if not (resolved / name).exists()]
    if still_missing:
        raise FileNotFoundError(
            f"Extracted {candidate} but still missing {still_missing} under {resolved}"
        )
    return resolved.resolve()


def read_entities(output_dir: Path) -> pd.DataFrame:
    entities = pd.read_parquet(output_dir / "entities.parquet")
    required = {"id", "title", "type"}
    missing = required - set(entities.columns)
    if missing:
        raise ValueError(f"entities.parquet missing columns: {sorted(missing)}")
    frame = entities.copy()
    frame["id"] = frame["id"].astype(str)
    frame["title"] = frame["title"].astype(str)
    frame["type"] = frame["type"].fillna("UNKNOWN").astype(str)
    return frame.reset_index(drop=True)


def read_relationships(output_dir: Path) -> pd.DataFrame:
    relationships = pd.read_parquet(output_dir / "relationships.parquet")
    required = {"source", "target"}
    missing = required - set(relationships.columns)
    if missing:
        raise ValueError(f"relationships.parquet missing columns: {sorted(missing)}")
    frame = relationships.copy()
    frame["source"] = frame["source"].astype(str)
    frame["target"] = frame["target"].astype(str)
    if "description" not in frame.columns:
        frame["description"] = ""
    else:
        frame["description"] = frame["description"].fillna("").astype(str)
    return frame.reset_index(drop=True)


def load_entity_vectors(output_dir: Path, entity_ids: list[str]) -> np.ndarray:
    try:
        import lancedb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("lancedb is required to load entity_description vectors") from exc

    db_uri = output_dir / "lancedb"
    if not db_uri.exists():
        raise FileNotFoundError(f"Missing LanceDB directory: {db_uri}")

    db = lancedb.connect(str(db_uri))
    listed = db.list_tables() if hasattr(db, "list_tables") else db.table_names()
    table_names = set(listed.tables if hasattr(listed, "tables") else listed)
    if ENTITY_EMBEDDING_TABLE not in table_names:
        raise FileNotFoundError(
            f"LanceDB table '{ENTITY_EMBEDDING_TABLE}' not found in {db_uri}"
        )

    table = db.open_table(ENTITY_EMBEDDING_TABLE)
    vectors_frame = table.to_pandas()
    if "id" not in vectors_frame.columns or "vector" not in vectors_frame.columns:
        raise ValueError(
            f"{ENTITY_EMBEDDING_TABLE} must contain 'id' and 'vector' columns"
        )

    by_id = {
        str(row.id): np.asarray(row.vector, dtype=np.float32)
        for row in vectors_frame[["id", "vector"]].itertuples(index=False)
    }
    missing = [entity_id for entity_id in entity_ids if entity_id not in by_id]
    if missing:
        sample = ", ".join(missing[:5])
        raise ValueError(
            f"{len(missing)} entity ids missing from {ENTITY_EMBEDDING_TABLE} "
            f"(sample: {sample})"
        )

    matrix = np.stack([by_id[entity_id] for entity_id in entity_ids], axis=0)
    if matrix.ndim != 2:
        raise ValueError(f"Unexpected embedding matrix shape: {matrix.shape}")
    return matrix


def cluster_metrics(
    titles: list[str],
    types: list[str],
    components: list[int],
    sample_limit: int,
) -> dict[str, Any]:
    groups: dict[int, list[int]] = defaultdict(list)
    for index, component in enumerate(components):
        groups[component].append(index)

    multi = [members for members in groups.values() if len(members) > 1]
    redundant_entities = sum(len(members) for members in multi)
    total = len(titles)
    samples = []
    for members in sorted(multi, key=len, reverse=True)[:sample_limit]:
        samples.append(
            {
                "size": len(members),
                "type": types[members[0]],
                "titles": sorted({titles[index] for index in members}),
            }
        )
    return {
        "entity_count": total,
        "cluster_count": len(groups),
        "multi_member_cluster_count": len(multi),
        "redundant_entity_count": redundant_entities,
        "entity_redundancy_rate": round(redundant_entities / total, 6) if total else 0.0,
        "cluster_samples": samples,
        "multi_member_indices": multi,
    }


def apply_lexical_unions(uf: UnionFind, titles: list[str], types: list[str]) -> None:
    buckets: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, (entity_type, title) in enumerate(zip(types, titles)):
        buckets[(entity_type, canonical_title(title))].append(index)
    for members in buckets.values():
        head = members[0]
        for other in members[1:]:
            uf.union(head, other)


def apply_embedding_unions(
    uf: UnionFind,
    types: list[str],
    vectors: np.ndarray,
    cosine_threshold: float,
) -> tuple[int, int]:
    if not 0.0 < cosine_threshold <= 1.0:
        raise ValueError("cosine_threshold must be in (0, 1]")

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    normalized = vectors / norms
    similarity = normalized @ normalized.T

    type_to_indices: dict[str, list[int]] = defaultdict(list)
    for index, entity_type in enumerate(types):
        type_to_indices[entity_type].append(index)

    pair_count = 0
    for indices in type_to_indices.values():
        if len(indices) < 2:
            continue
        index_array = np.asarray(indices, dtype=np.int32)
        block = similarity[np.ix_(index_array, index_array)]
        rows, cols = np.where(np.triu(block, k=1) >= cosine_threshold)
        for row, col in zip(rows.tolist(), cols.tolist()):
            uf.union(int(index_array[row]), int(index_array[col]))
            pair_count += 1
    return pair_count, int(vectors.shape[1])


def lexical_entity_redundancy(
    entities: pd.DataFrame, sample_limit: int
) -> dict[str, Any]:
    titles = entities["title"].tolist()
    types = entities["type"].tolist()
    uf = UnionFind.create(len(entities))
    apply_lexical_unions(uf, titles, types)
    components = [uf.find(index) for index in range(len(entities))]
    metrics = cluster_metrics(titles, types, components, sample_limit)
    metrics["method"] = "lexical_canonical_title_within_type"
    metrics.pop("multi_member_indices", None)
    return metrics


def embedding_entity_redundancy(
    entities: pd.DataFrame,
    vectors: np.ndarray,
    cosine_threshold: float,
    sample_limit: int,
) -> dict[str, Any]:
    titles = entities["title"].tolist()
    types = entities["type"].tolist()
    uf = UnionFind.create(len(entities))
    pair_count, embedding_dim = apply_embedding_unions(
        uf, types, vectors, cosine_threshold
    )
    components = [uf.find(index) for index in range(len(entities))]
    metrics = cluster_metrics(titles, types, components, sample_limit)
    metrics["method"] = "cosine_connected_components_within_type"
    metrics["cosine_threshold"] = cosine_threshold
    metrics["similar_pair_count"] = pair_count
    metrics["embedding_dim"] = embedding_dim
    # Keep indices only for combined union; strip before JSON serialize via build_report.
    return metrics


def combined_entity_redundancy(
    entities: pd.DataFrame,
    vectors: np.ndarray,
    cosine_threshold: float,
    sample_limit: int,
) -> dict[str, Any]:
    titles = entities["title"].tolist()
    types = entities["type"].tolist()
    uf = UnionFind.create(len(entities))
    apply_lexical_unions(uf, titles, types)
    apply_embedding_unions(uf, types, vectors, cosine_threshold)
    components = [uf.find(index) for index in range(len(entities))]
    metrics = cluster_metrics(titles, types, components, sample_limit)
    metrics["method"] = "lexical_or_embedding_union"
    metrics.pop("multi_member_indices", None)
    return metrics


def relation_redundancy(
    relationships: pd.DataFrame, sample_limit: int = 50
) -> dict[str, Any]:
    total = len(relationships)
    self_loop_mask = relationships["source"] == relationships["target"]
    self_loop_count = int(self_loop_mask.sum())

    pair_groups = relationships.groupby(["source", "target"], sort=False)
    duplicate_extra_count = 0
    conflicting_pair_count = 0
    duplicate_pair_count = 0
    duplicate_samples: list[dict[str, Any]] = []
    self_loop_samples: list[dict[str, Any]] = []

    for (source, target), group in pair_groups:
        size = len(group)
        if source == target:
            if len(self_loop_samples) < sample_limit:
                self_loop_samples.append(
                    {
                        "source": source,
                        "target": target,
                        "count": size,
                        "descriptions": group["description"].head(3).tolist(),
                    }
                )
            continue
        if size <= 1:
            continue
        duplicate_pair_count += 1
        duplicate_extra_count += size - 1
        distinct_descriptions = {
            text.strip() for text in group["description"].tolist() if text.strip()
        }
        if len(distinct_descriptions) > 1:
            conflicting_pair_count += 1
        if len(duplicate_samples) < sample_limit:
            duplicate_samples.append(
                {
                    "source": source,
                    "target": target,
                    "count": size,
                    "distinct_description_count": len(distinct_descriptions),
                    "descriptions": group["description"].head(3).tolist(),
                }
            )

    redundant_count = self_loop_count + duplicate_extra_count
    return {
        "relationship_count": total,
        "self_loop_count": self_loop_count,
        "duplicate_pair_count": duplicate_pair_count,
        "duplicate_extra_count": duplicate_extra_count,
        "conflicting_pair_count": conflicting_pair_count,
        "redundant_relationship_count": redundant_count,
        "relation_redundancy_rate": round(redundant_count / total, 6) if total else 0.0,
        "self_loop_samples": self_loop_samples,
        "duplicate_pair_samples": duplicate_samples,
    }


def public_entity_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "multi_member_indices"}


def build_report(
    output_dir: Path,
    cosine_threshold: float,
    sample_limit: int,
) -> dict[str, Any]:
    entities = read_entities(output_dir)
    relationships = read_relationships(output_dir)
    vectors = load_entity_vectors(output_dir, entities["id"].tolist())

    lexical = lexical_entity_redundancy(entities, sample_limit)
    embedding = embedding_entity_redundancy(
        entities, vectors, cosine_threshold, sample_limit
    )
    combined = combined_entity_redundancy(
        entities, vectors, cosine_threshold, sample_limit
    )
    relations = relation_redundancy(relationships, sample_limit)

    return {
        "output_dir": str(output_dir),
        "notes": {
            "entity_redundancy": (
                "Automated approximation of docs/metric.md Entity Redundancy Rate. "
                "No manual synonym labels. Primary rate uses same-type description "
                "embedding connected components; lexical rate uses canonical titles; "
                "combined unions both. Lower cosine thresholds raise recall for "
                "aliases but may also cluster related-but-distinct entities "
                "(for example ATLAS parent/child techniques)."
            ),
            "relation_redundancy": (
                "Self-loops plus extra edges beyond one for each (source, target) pair, "
                "divided by total relationships."
            ),
            "read_only": True,
        },
        "entity_redundancy": {
            "primary_rate": embedding["entity_redundancy_rate"],
            "lexical": lexical,
            "embedding": public_entity_metrics(embedding),
            "combined": combined,
        },
        "relation_redundancy": relations,
    }


def render_markdown(report: dict[str, Any]) -> str:
    entity = report["entity_redundancy"]
    lexical = entity["lexical"]
    embedding = entity["embedding"]
    combined = entity["combined"]
    relation = report["relation_redundancy"]
    lines = [
        "# GraphRAG 冗余率评估",
        "",
        f"- output: `{report['output_dir']}`",
        "- 只读评估：不修改图谱，不采集新语料，不人工标注。",
        "",
        "## Entity Redundancy Rate",
        "",
        f"- 主指标（嵌入聚类）: **{embedding['entity_redundancy_rate']:.4%}**",
        f"- 词面归一化: {lexical['entity_redundancy_rate']:.4%}",
        f"- 合并（词面 ∪ 嵌入）: {combined['entity_redundancy_rate']:.4%}",
        f"- 实体总数: {embedding['entity_count']}",
        f"- 嵌入阈值 cosine ≥ {embedding['cosine_threshold']}",
        f"- 多成员簇数（嵌入）: {embedding['multi_member_cluster_count']}",
        f"- 落入多成员簇的实体数（嵌入）: {embedding['redundant_entity_count']}",
        "",
        "### 嵌入簇样本",
        "",
    ]
    if embedding["cluster_samples"]:
        for sample in embedding["cluster_samples"][:15]:
            titles = ", ".join(sample["titles"][:8])
            lines.append(f"- [{sample['type']}] size={sample['size']}: {titles}")
    else:
        lines.append("- （无）")

    lines.extend(
        [
            "",
            "## Relation Redundancy Rate",
            "",
            f"- 主指标: **{relation['relation_redundancy_rate']:.4%}**",
            f"- 关系总数: {relation['relationship_count']}",
            f"- 自环: {relation['self_loop_count']}",
            f"- 重复实体对: {relation['duplicate_pair_count']}",
            f"- 重复多余边: {relation['duplicate_extra_count']}",
            f"- 同对多描述（冲突候选）: {relation['conflicting_pair_count']}",
            f"- 冗余关系数: {relation['redundant_relationship_count']}",
            "",
            "详细样本见 `reports/redundancy_metrics.json`。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_dir = (args.output_dir or root / "output").resolve()
    reports_dir = (args.reports_dir or root / "reports").resolve()
    zip_path = args.zip.resolve() if args.zip else None

    resolved_output = ensure_output_dir(root, output_dir, zip_path)
    report = build_report(
        resolved_output,
        cosine_threshold=args.cosine_threshold,
        sample_limit=args.cluster_sample_limit,
    )

    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "redundancy_metrics.json"
    md_path = reports_dir / "redundancy_metrics.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")

    summary = {
        "entity_redundancy_rate": report["entity_redundancy"]["primary_rate"],
        "lexical_entity_redundancy_rate": report["entity_redundancy"]["lexical"][
            "entity_redundancy_rate"
        ],
        "combined_entity_redundancy_rate": report["entity_redundancy"]["combined"][
            "entity_redundancy_rate"
        ],
        "relation_redundancy_rate": report["relation_redundancy"][
            "relation_redundancy_rate"
        ],
        "json": str(json_path),
        "markdown": str(md_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
