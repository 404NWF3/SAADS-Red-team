"""Validated data exchanged by the attack case generator."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    model_validator,
)

SupportedAttackFamily: TypeAlias = Literal[
    "prompt_injection",
    "long_horizon_dialogue",
    "tool_hijack",
]
AttackFamily: TypeAlias = SupportedAttackFamily | Literal["unsupported"]
QueryPurpose: TypeAlias = Literal[
    "intent_classification",
    "case_grounding",
    "script_grounding",
    "threat_modeling",
    "hypothesis_grounding",
    "adjudication_grounding",
    "test_grounding",
]

FIXED_SAFETY_CONSTRAINTS = (
    "offline_only",
    "mock_target_only",
    "no_network",
    "no_system_commands",
    "no_external_file_mutation",
)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class IntentDecision(ContractModel):
    family: AttackFamily
    target_surface: str
    objective: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)
    missing_context: list[str]

    @model_validator(mode="after")
    def require_supported_intent_details(self) -> IntentDecision:
        if self.family != "unsupported" and (
            not self.target_surface or not self.objective
        ):
            raise ValueError(
                "supported intent requires target_surface and objective"
            )
        return self


class GraphEvidence(ContractModel):
    evidence_id: str = Field(min_length=1)
    purpose: QueryPurpose
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class AttackPayload(ContractModel):
    payload_id: str = Field(min_length=1)
    delivery_role: str = Field(min_length=1)
    content: str = Field(min_length=1)
    expected_effect: str = Field(min_length=1)


class SimulationStep(ContractModel):
    order: int = Field(ge=1)
    action: str = Field(min_length=1)
    expected_observable: str = Field(min_length=1)


class PromptInjectionScriptPlan(ContractModel):
    family: Literal["prompt_injection"]
    user_query: str = Field(min_length=1)
    trusted_context: str = Field(min_length=1)
    injected_context: str = Field(min_length=1)
    injected_instruction: str = Field(min_length=1)
    expected_baseline: str = Field(min_length=1)
    expected_attack_delta: str = Field(min_length=1)


class DialogueTurn(ContractModel):
    turn: int = Field(ge=1)
    user_message: str = Field(min_length=1)
    escalation_stage: str = Field(min_length=1)


class LongHorizonDialogueScriptPlan(ContractModel):
    family: Literal["long_horizon_dialogue"]
    system_rule: str = Field(min_length=1)
    turns: list[DialogueTurn] = Field(min_length=1)
    safety_checkpoints: list[str] = Field(min_length=1)
    expected_state_delta: str = Field(min_length=1)


class ToolHijackScriptPlan(ContractModel):
    family: Literal["tool_hijack"]
    allowed_tool: str = Field(min_length=1)
    poisoned_tool_description: str = Field(min_length=1)
    requested_arguments: dict[str, JsonValue]
    forbidden_arguments: dict[str, JsonValue]
    expected_planned_call: dict[str, JsonValue]
    execution_permitted: Literal[False] = False


ScriptPlan: TypeAlias = Annotated[
    PromptInjectionScriptPlan
    | LongHorizonDialogueScriptPlan
    | ToolHijackScriptPlan,
    Field(discriminator="family"),
]


class AttackCaseDraft(ContractModel):
    title: str = Field(min_length=1)
    target_surface: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    preconditions: list[str] = Field(min_length=1)
    payloads: list[AttackPayload] = Field(min_length=1)
    simulation_steps: list[SimulationStep] = Field(min_length=1)
    observables: list[str] = Field(min_length=1)
    success_criteria: list[str] = Field(min_length=1)
    failure_signals: list[str] = Field(min_length=1)
    script_plan: ScriptPlan


class AttackCase(AttackCaseDraft):
    schema_version: Literal["1.0"]
    case_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    source_request: str = Field(min_length=1)
    family: SupportedAttackFamily
    safety_constraints: list[str]
    graphrag_evidence: list[GraphEvidence]

    @model_validator(mode="after")
    def enforce_case_invariants(self) -> AttackCase:
        if self.case_id in {".", ".."}:
            raise ValueError("case_id must be a safe directory name")
        if self.script_plan.family != self.family:
            raise ValueError("script plan family must match attack case family")
        if tuple(self.safety_constraints) != FIXED_SAFETY_CONSTRAINTS:
            raise ValueError("attack case must contain the fixed safety constraints")
        return self


class GeneratedAttackPackage(ContractModel):
    case: AttackCase
    script_source: str = Field(min_length=1)
    query_audit: list[GraphEvidence]


class ArtifactPaths(ContractModel):
    directory: Path
    case_json: Path
    script: Path
