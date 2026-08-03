from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError
import yaml


ALLOWED_ENTITY_TYPES = {
    "ATTACK_TECHNIQUE",
    "DEFENSE_CONTROL",
    "COMPONENT",
    "VULNERABILITY",
    "TOOL",
    "STANDARD",
    "EVALUATION",
}


def normalize_title(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).upper().strip()
    return re.sub(r"\s+", " ", normalized)


def lexical_signature(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", "", normalize_title(value))


@dataclass(frozen=True)
class AlignmentDecision:
    source_title: str
    source_type: str
    canonical_title: str
    canonical_type: str
    method: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class AlignmentResult:
    entities: pd.DataFrame
    relationships: pd.DataFrame
    audit: pd.DataFrame


class AlignmentError(ValueError):
    """Raised when an alignment decision would make the graph ambiguous."""


@dataclass(frozen=True)
class EntityCandidate:
    title: str
    entity_type: str
    description: str


class GlmAlignmentResponse(BaseModel):
    canonical_title: str
    canonical_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class GlmAmbiguityResolver:
    def __init__(self, completion: Any, minimum_confidence: float = 0.90) -> None:
        self._completion = completion
        self._minimum_confidence = minimum_confidence

    async def resolve(
        self, candidates: list[EntityCandidate]
    ) -> list[AlignmentDecision]:
        candidate_payload = [
            {
                "candidate_id": index,
                "title": normalize_title(candidate.title),
                "type": normalize_title(candidate.entity_type),
                "description": candidate.description,
            }
            for index, candidate in enumerate(candidates)
        ]
        messages = [
            {
                "role": "system",
                "content": (
                    "You choose one canonical node for a GraphRAG security graph. "
                    "All candidates have the same punctuation-insensitive title "
                    "signature. GraphRAG relationship endpoints contain titles "
                    "but not types, so the group must resolve to one title and "
                    "one semantic type. Choose a title exactly as supplied by a "
                    "candidate and the type best supported by the descriptions. "
                    "Do not invent a new title or type. Return only one JSON "
                    "object with exactly these four keys: canonical_title, "
                    "canonical_type, confidence, reason. Do not echo the input, "
                    "the candidate list, or an output schema. Example shape: "
                    '{"canonical_title":"EXACT SUPPLIED TITLE",'
                    '"canonical_type":"COMPONENT","confidence":0.95,'
                    '"reason":"brief evidence-based explanation"}.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "allowed_entity_types": sorted(ALLOWED_ENTITY_TYPES),
                        "candidates": candidate_payload,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        response = None
        for attempt in range(2):
            attempt_messages = list(messages)
            if attempt:
                attempt_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous output did not match the required four-key "
                            "JSON object. Return only canonical_title, canonical_type, "
                            "confidence, and reason now."
                        ),
                    }
                )
            try:
                response = await self._completion.completion_async(
                    messages=attempt_messages,
                    response_format=GlmAlignmentResponse,
                    temperature=0,
                    max_completion_tokens=2000,
                )
                break
            except ValidationError as exc:
                if attempt:
                    raise AlignmentError(
                        "GLM returned invalid structured output twice"
                    ) from exc
        if response is None:
            raise AlignmentError("GLM did not return a response")
        structured = getattr(response, "formatted_response", None)
        if not isinstance(structured, GlmAlignmentResponse):
            raise AlignmentError("GLM did not return a structured response")

        canonical_title = normalize_title(structured.canonical_title)
        supplied_titles = {
            normalize_title(candidate.title) for candidate in candidates
        }
        if canonical_title not in supplied_titles:
            raise AlignmentError(
                f"GLM invented canonical title {canonical_title!r}"
            )
        canonical_type = normalize_title(structured.canonical_type)
        if canonical_type not in ALLOWED_ENTITY_TYPES:
            raise AlignmentError(
                f"GLM returned invalid entity type {canonical_type!r}"
            )

        accepted = structured.confidence >= self._minimum_confidence
        results: list[AlignmentDecision] = []
        for candidate in candidates:
            source_title = normalize_title(candidate.title)
            source_type = normalize_title(candidate.entity_type)
            results.append(
                AlignmentDecision(
                    source_title=source_title,
                    source_type=source_type,
                    canonical_title=(
                        canonical_title if accepted else source_title
                    ),
                    canonical_type=canonical_type if accepted else source_type,
                    method="glm" if accepted else "glm_review_required",
                    confidence=structured.confidence,
                    reason=structured.reason,
                )
            )
        return results


class EntityRegistry:
    def __init__(
        self,
        typed_aliases: dict[tuple[str, str], tuple[str, str]],
        untyped_aliases: dict[str, tuple[str, str]],
    ) -> None:
        self._typed_aliases = typed_aliases
        self._untyped_aliases = untyped_aliases

    def resolve(
        self, title: object, entity_type: object
    ) -> AlignmentDecision | None:
        source_title = normalize_title(title)
        source_type = normalize_title(entity_type)
        target = self._typed_aliases.get((source_title, source_type))
        if target is None:
            target = self._untyped_aliases.get(source_title)
        if target is None:
            return None
        return AlignmentDecision(
            source_title=source_title,
            source_type=source_type,
            canonical_title=target[0],
            canonical_type=target[1],
            method="registry",
            confidence=1.0,
            reason="Versioned canonical entity registry",
        )


def load_entity_registry(path: Path) -> EntityRegistry:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    entities = data["canonical_entities"]
    typed_aliases: dict[tuple[str, str], tuple[str, str]] = {}
    untyped_aliases: dict[str, tuple[str, str]] = {}

    for raw_canonical_title, specification in entities.items():
        canonical_title = normalize_title(raw_canonical_title)
        canonical_type = normalize_title(specification["type"])
        target = (canonical_title, canonical_type)
        for raw_alias in specification["aliases"]:
            if isinstance(raw_alias, dict):
                alias = normalize_title(raw_alias["title"])
                source_type = normalize_title(raw_alias["source_type"])
                typed_aliases[(alias, source_type)] = target
            else:
                alias = normalize_title(raw_alias)
                untyped_aliases[alias] = target

    return EntityRegistry(typed_aliases, untyped_aliases)


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        converted = value.tolist()  # type: ignore[union-attr]
        return converted if isinstance(converted, list) else [converted]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _unique(values: list[object]) -> list[object]:
    result: list[object] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _merge_descriptions(values: pd.Series) -> str:
    descriptions: list[object] = []
    for value in values:
        descriptions.extend(_as_list(value))
    return "\n\n".join(
        str(value).strip()
        for value in _unique(descriptions)
        if str(value).strip()
    )


def _merge_ids(values: pd.Series) -> list[object]:
    identifiers: list[object] = []
    for value in values:
        identifiers.extend(_as_list(value))
    return _unique(identifiers)


async def align_graph_tables(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    registry: EntityRegistry,
    resolver: Any | None = None,
) -> AlignmentResult:
    aligned_entities = entities.copy()
    decisions: list[AlignmentDecision] = []

    for row in aligned_entities[["title", "type"]].itertuples(index=False):
        source_title = normalize_title(row.title)
        source_type = normalize_title(row.type)
        decision = registry.resolve(source_title, source_type)
        if decision is None:
            decision = AlignmentDecision(
                source_title=source_title,
                source_type=source_type,
                canonical_title=source_title,
                canonical_type=source_type,
                method="identity",
                confidence=1.0,
                reason="No alias rule applied",
            )
        decisions.append(decision)

    if resolver is not None:
        unresolved_by_signature: dict[str, list[int]] = {}
        for index, decision in enumerate(decisions):
            if decision.method == "identity":
                unresolved_by_signature.setdefault(
                    lexical_signature(decision.source_title), []
                ).append(index)
        for indices in unresolved_by_signature.values():
            candidate_indices: dict[tuple[str, str], list[int]] = {}
            for index in indices:
                key = (
                    decisions[index].source_title,
                    decisions[index].source_type,
                )
                candidate_indices.setdefault(key, []).append(index)
            if len(candidate_indices) < 2:
                continue
            candidates = [
                EntityCandidate(
                    title=source_title,
                    entity_type=source_type,
                    description=_merge_descriptions(
                        pd.Series(
                            [
                                aligned_entities.iloc[index]["description"]
                                for index in source_indices
                            ]
                        )
                    ),
                )
                for (source_title, source_type), source_indices
                in candidate_indices.items()
            ]
            resolved = await resolver.resolve(candidates)
            resolved_by_source = {
                (
                    normalize_title(decision.source_title),
                    normalize_title(decision.source_type),
                ): decision
                for decision in resolved
            }
            for source_key, source_indices in candidate_indices.items():
                if source_key not in resolved_by_source:
                    raise AlignmentError(
                        f"Resolver omitted alignment decision for {source_key}"
                    )
                for index in source_indices:
                    decisions[index] = resolved_by_source[source_key]

    title_targets: dict[str, tuple[str, str]] = {}
    for decision in decisions:
        source_title = decision.source_title
        previous = title_targets.get(source_title)
        target = (decision.canonical_title, decision.canonical_type)
        if previous is not None and previous != target:
            raise ValueError(
                f"Entity title {source_title!r} resolves to multiple canonical targets"
            )
        title_targets[source_title] = target

    aligned_entities["title"] = [
        decision.canonical_title for decision in decisions
    ]
    aligned_entities["type"] = [
        decision.canonical_type for decision in decisions
    ]
    entity_aggregations: dict[str, object] = {
        "description": ("description", _merge_descriptions),
        "text_unit_ids": ("text_unit_ids", _merge_ids),
        "frequency": ("frequency", "sum"),
    }
    aligned_entities = (
        aligned_entities.groupby(["title", "type"], sort=False)
        .agg(**entity_aggregations)
        .reset_index()
    )

    aligned_relationships = relationships.copy()
    aligned_relationships["source"] = aligned_relationships["source"].map(
        lambda value: title_targets[normalize_title(value)][0]
    )
    aligned_relationships["target"] = aligned_relationships["target"].map(
        lambda value: title_targets[normalize_title(value)][0]
    )
    aligned_relationships = aligned_relationships[
        aligned_relationships["source"] != aligned_relationships["target"]
    ]
    relationship_aggregations: dict[str, object] = {
        "description": ("description", _merge_descriptions),
        "text_unit_ids": ("text_unit_ids", _merge_ids),
        "weight": ("weight", "sum"),
    }
    aligned_relationships = (
        aligned_relationships.groupby(["source", "target"], sort=False)
        .agg(**relationship_aggregations)
        .reset_index()
    )

    audit = pd.DataFrame(
        [
            {
                "source_title": decision.source_title,
                "source_type": decision.source_type,
                "canonical_title": decision.canonical_title,
                "canonical_type": decision.canonical_type,
                "method": decision.method,
                "confidence": decision.confidence,
                "reason": decision.reason,
            }
            for decision in decisions
        ]
    )
    return AlignmentResult(
        entities=aligned_entities,
        relationships=aligned_relationships,
        audit=audit,
    )
