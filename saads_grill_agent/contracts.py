"""Validated contracts for the adversarial repository grill assessment."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


HypothesisStatus: TypeAlias = Literal[
    "proposed", "debating", "confirmed", "rejected", "duplicate",
]
AdjudicationVerdict: TypeAlias = Literal[
    "confirm", "reject", "request_more_evidence", "duplicate",
]
GraphReviewPurpose: TypeAlias = Literal[
    "threat_modeling", "hypothesis_grounding",
    "adjudication_grounding", "test_grounding",
]
AssessmentPhase: TypeAlias = Literal[
    "intake", "profiling", "discovery", "debating",
    "adjudicating", "generating_tests", "complete", "interrupted",
]
Severity: TypeAlias = Literal["critical", "high", "medium", "low"]
ConfidenceLevel: TypeAlias = Literal["high", "medium", "low"]
TestLanguage: TypeAlias = Literal["python", "typescript", "javascript"]
TestFramework: TypeAlias = Literal["pytest", "vitest", "jest"]


class SdkLimits(ContractModel):
    """Claude Agent SDK turn/budget knobs. ``None`` max_turns means unlimited."""

    team_max_turns: int | None = Field(default=None, ge=1)
    discovery_max_turns: int | None = Field(default=None, ge=1)
    debate_max_turns: int | None = Field(default=None, ge=1)
    judge_max_turns: int | None = Field(default=None, ge=1)
    # ``None`` = do not pass a per-turn SDK budget cap.
    team_budget_usd: float | None = Field(default=5.0, gt=0, le=500)
    judge_budget_usd: float | None = Field(default=2.0, gt=0, le=500)
    enable_subagents_profiling: bool = False
    enable_subagents_discovery: bool = False
    enable_subagents_debate: bool = False


class AssessmentConfig(ContractModel):
    target_repo: Path
    goal: str = "审查该 LLM 应用的代码级安全漏洞"
    supplied_model_provider: str | None = None
    supplied_model_name: str | None = None
    supplied_agent_framework: str | None = None
    supplied_frontend_roots: list[str] = Field(default_factory=list)
    supplied_backend_roots: list[str] = Field(default_factory=list)
    scope_includes: list[str] = Field(default_factory=list)
    scope_excludes: list[str] = Field(default_factory=list)
    max_rounds_per_hypothesis: int = Field(default=4, ge=1, le=12)
    max_threat_surfaces: int = Field(default=20, ge=1, le=100)
    max_hypotheses: int = Field(default=40, ge=1, le=200)
    # ``None`` = no orchestrator team-turn scheduling ceiling.
    max_agent_calls: int | None = Field(default=100, ge=5, le=10000)
    # ``None`` = no global assessment cost ceiling.
    max_cost_usd: float | None = Field(default=25.0, gt=0, le=500)
    use_graphrag: bool = True
    sdk: SdkLimits = Field(default_factory=SdkLimits)


class RepositoryProfile(ContractModel):
    snapshot_id: str
    model_provider: str
    model_name: str
    agent_framework: str
    frontend_roots: list[str]
    backend_roots: list[str]
    model_call_sites: list[str]
    prompt_assembly_sites: list[str]
    tool_definition_sites: list[str]
    retrieval_and_ingestion_sites: list[str]
    memory_sites: list[str]
    authn_authz_sites: list[str]
    output_interpretation_sites: list[str]
    test_frameworks: list[Literal["pytest", "vitest", "jest"]]
    profile_evidence_ids: list[str] = Field(min_length=1)
    supplied_profile_conflicts: list[str]


class ThreatSurface(ContractModel):
    surface_id: str
    kind: Literal[
        "prompt_boundary", "rag_ingestion", "rag_retrieval", "memory",
        "tool_call", "model_output", "frontend", "backend",
        "identity_authorization", "secret_config", "supply_chain",
    ]
    name: str
    entrypoints: list[str] = Field(min_length=1)
    trust_transition: str
    assets: list[str] = Field(min_length=1)
    code_evidence_ids: list[str] = Field(min_length=1)


class CodeEvidence(ContractModel):
    evidence_id: str
    relative_path: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    excerpt: str = Field(min_length=1, max_length=4000)
    claim: str = Field(min_length=1)


class VulnerabilityHypothesis(ContractModel):
    hypothesis_id: str
    surface_id: str
    title: str
    root_cause: str
    attack_path: list[str] = Field(min_length=1)
    impact: str
    preconditions: list[str]
    code_evidence_ids: list[str] = Field(default_factory=list)
    graph_evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_one_autonomous_evidence_source(self) -> VulnerabilityHypothesis:
        if not self.code_evidence_ids and not self.graph_evidence_ids:
            raise ValueError("hypothesis requires at least one signed evidence")
        return self


class HypothesisRecord(ContractModel):
    hypothesis: VulnerabilityHypothesis
    status: HypothesisStatus
    final_adjudication_id: str | None

    @model_validator(mode="after")
    def require_adjudication_for_terminal_status(self) -> HypothesisRecord:
        terminal = {"confirmed", "rejected", "duplicate"}
        if self.status in terminal and not self.final_adjudication_id:
            raise ValueError("terminal hypothesis status requires adjudication")
        return self


class DefenderRebuttal(ContractModel):
    hypothesis_id: str
    round_number: int = Field(ge=1)
    disposition: Literal[
        "refute", "mitigated", "unreachable", "concede", "insufficient_evidence"
    ]
    arguments: list[str] = Field(min_length=1)
    new_code_evidence_ids: list[str]
    unresolved_conditions: list[str]


class RedResponse(ContractModel):
    hypothesis_id: str
    round_number: int = Field(ge=1)
    disposition: Literal["withdraw", "refine", "stand"]
    reasoning: list[str] = Field(min_length=1)
    revised_hypothesis: VulnerabilityHypothesis | None
    new_code_evidence_ids: list[str]
    new_graph_evidence_ids: list[str]


class Adjudication(ContractModel):
    adjudication_id: str = Field(min_length=1)
    hypothesis_id: str
    round_number: int = Field(ge=1)
    verdict: AdjudicationVerdict
    rationale: list[str] = Field(min_length=1)
    accepted_code_evidence_ids: list[str]
    accepted_graph_evidence_ids: list[str]
    missing_proof: list[str]
    duplicate_of: str | None
    confidence: float = Field(ge=0.0, le=1.0)


class Finding(ContractModel):
    finding_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    severity: Severity
    confidence: ConfidenceLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    root_cause: str = Field(min_length=1)
    attack_path: list[str] = Field(min_length=1)
    impact: str = Field(min_length=1)
    preconditions: list[str]
    code_evidence_ids: list[str] = Field(default_factory=list)
    graph_evidence_ids: list[str] = Field(default_factory=list)
    judge_rationale: list[str] = Field(min_length=1)
    strongest_rebuttal: list[str] = Field(default_factory=list)
    rebuttal_failure_reason: str = ""
    remediation: str = Field(min_length=1)
    generated_test_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_one_signed_evidence(self) -> Finding:
        if not self.code_evidence_ids and not self.graph_evidence_ids:
            raise ValueError("finding requires at least one signed evidence")
        return self


class GeneratedTestDraft(ContractModel):
    test_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    language: TestLanguage
    framework: TestFramework
    suggested_target_path: str = Field(min_length=1)
    source: str = Field(min_length=1)
    expected_failing_assertion: str = Field(min_length=1)
    mocked_dependencies: list[str] = Field(default_factory=list)
    required_fixtures: list[str] = Field(default_factory=list)
    suggested_run_command: str = Field(min_length=1)


class DiscoveryTracker(ContractModel):
    consecutive_empty_sweeps: int = Field(default=0, ge=0)


class AssessmentState(ContractModel):
    config: AssessmentConfig
    snapshot_id: str
    phase: AssessmentPhase = "intake"
    profile: RepositoryProfile | None = None
    threat_surfaces: list[ThreatSurface] = Field(default_factory=list)
    hypotheses: dict[str, HypothesisRecord] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    agent_calls_used: int = Field(default=0, ge=0)
    cost_usd_used: float = Field(default=0.0, ge=0)
    discovery: DiscoveryTracker = Field(default_factory=DiscoveryTracker)
    team_sessions: dict[str, str] = Field(default_factory=dict)
    graph_enabled: bool = False
    graph_skipped_reason: str | None = None

    def register_evidence(self, *evidence_ids: str) -> None:
        for evidence_id in evidence_ids:
            if evidence_id not in self.evidence_ids:
                self.evidence_ids.append(evidence_id)

    def apply_adjudication(self, adjudication: Adjudication) -> HypothesisRecord:
        record = self.hypotheses.get(adjudication.hypothesis_id)
        if record is None:
            raise ValueError(
                f"unknown hypothesis: {adjudication.hypothesis_id}"
            )
        for evidence_id in (
            adjudication.accepted_code_evidence_ids
            + adjudication.accepted_graph_evidence_ids
        ):
            if evidence_id not in self.evidence_ids:
                raise ValueError(f"unknown evidence id: {evidence_id}")

        terminal_status = {
            "confirm": "confirmed",
            "reject": "rejected",
            "duplicate": "duplicate",
        }
        if adjudication.verdict == "request_more_evidence":
            new_status: HypothesisStatus = "debating"
            final_adjudication_id: str | None = None
        else:
            new_status = terminal_status[adjudication.verdict]
            final_adjudication_id = adjudication.adjudication_id

        updated = HypothesisRecord(
            hypothesis=record.hypothesis,
            status=new_status,
            final_adjudication_id=final_adjudication_id,
        )
        self.hypotheses[adjudication.hypothesis_id] = updated
        return updated
