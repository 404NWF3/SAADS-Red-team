from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from saads_grill_agent.contracts import (
    Adjudication,
    AssessmentConfig,
    AssessmentState,
    CodeEvidence,
    DefenderRebuttal,
    Finding,
    GeneratedTestDraft,
    HypothesisRecord,
    RedResponse,
    RepositoryProfile,
    ThreatSurface,
    VulnerabilityHypothesis,
)


def vulnerability_hypothesis() -> VulnerabilityHypothesis:
    return VulnerabilityHypothesis(
        hypothesis_id="hyp-1",
        surface_id="surf-1",
        title="Indirect prompt injection via RAG context",
        root_cause="Untrusted retrieval content is concatenated with trusted instructions.",
        attack_path=[
            "attacker controls a retrieved document",
            "model obeys the injected instruction",
        ],
        impact="Instruction hijack revealing protected data.",
        preconditions=["retrieval returns attacker-controlled content"],
        code_evidence_ids=["code-1"],
        graph_evidence_ids=[],
    )


def valid_finding_dict() -> dict:
    return {
        "finding_id": "finding-1",
        "hypothesis_id": "hyp-1",
        "severity": "high",
        "confidence": "medium",
        "confidence_score": 0.7,
        "root_cause": "Untrusted context concatenated with trusted instructions.",
        "attack_path": [
            "attacker controls retrieved context",
            "model obeys injected instruction",
        ],
        "impact": "Instruction hijack.",
        "preconditions": ["retrieval returns attacker content"],
        "code_evidence_ids": ["code-1"],
        "graph_evidence_ids": ["threat_modeling-abc"],
        "judge_rationale": ["The attack path is reachable via signed evidence."],
        "strongest_rebuttal": ["A partial filter exists."],
        "rebuttal_failure_reason": "The filter is bypassable.",
        "remediation": "Separate provenance of trusted and untrusted context.",
        "generated_test_ids": ["test-1"],
    }


def state_with_debating_hypothesis() -> AssessmentState:
    state = AssessmentState(
        config=AssessmentConfig(target_repo=Path("/repo")),
        snapshot_id="snap-1",
        phase="debating",
    )
    state.register_evidence("code-1", "graph-1")
    state.hypotheses["hyp-1"] = HypothesisRecord(
        hypothesis=vulnerability_hypothesis(),
        status="debating",
        final_adjudication_id=None,
    )
    return state


def test_only_adjudication_can_finalize_a_hypothesis() -> None:
    hypothesis = vulnerability_hypothesis()
    with pytest.raises(ValidationError, match="adjudication"):
        HypothesisRecord(
            hypothesis=hypothesis,
            status="confirmed",
            final_adjudication_id=None,
        )


def test_finding_requires_judge_rationale_and_confidence_score() -> None:
    payload = valid_finding_dict()
    del payload["judge_rationale"]
    with pytest.raises(ValidationError):
        Finding.model_validate(payload)

    payload = valid_finding_dict()
    del payload["confidence_score"]
    with pytest.raises(ValidationError):
        Finding.model_validate(payload)

    payload = valid_finding_dict()
    payload["confidence_score"] = 1.5
    with pytest.raises(ValidationError):
        Finding.model_validate(payload)

    payload = valid_finding_dict()
    payload["judge_rationale"] = []
    with pytest.raises(ValidationError):
        Finding.model_validate(payload)


def test_confirmed_finding_accepts_either_code_or_graph_evidence() -> None:
    finding = Finding.model_validate({
        **valid_finding_dict(),
        "code_evidence_ids": ["code-1"],
        "graph_evidence_ids": [],
    })
    assert finding.code_evidence_ids == ["code-1"]


def test_confirmed_finding_rejects_an_evidence_free_decision() -> None:
    with pytest.raises(ValidationError, match="at least one signed evidence"):
        Finding.model_validate({
            **valid_finding_dict(),
            "code_evidence_ids": [],
            "graph_evidence_ids": [],
        })


def test_finding_accepts_graph_only_evidence() -> None:
    finding = Finding.model_validate({
        **valid_finding_dict(),
        "code_evidence_ids": [],
        "graph_evidence_ids": ["threat_modeling-abc"],
    })
    assert finding.graph_evidence_ids == ["threat_modeling-abc"]


def test_hypothesis_requires_at_least_one_signed_evidence() -> None:
    with pytest.raises(ValidationError, match="at least one signed evidence"):
        VulnerabilityHypothesis(
            hypothesis_id="hyp-x",
            surface_id="surf-1",
            title="x",
            root_cause="x",
            attack_path=["x"],
            impact="x",
            preconditions=[],
            code_evidence_ids=[],
            graph_evidence_ids=[],
        )


def test_apply_adjudication_confirm_finalizes_hypothesis() -> None:
    state = state_with_debating_hypothesis()
    adjudication = Adjudication(
        adjudication_id="adj-1",
        hypothesis_id="hyp-1",
        round_number=1,
        verdict="confirm",
        rationale=["The attack path is reachable."],
        accepted_code_evidence_ids=["code-1"],
        accepted_graph_evidence_ids=[],
        missing_proof=[],
        duplicate_of=None,
        confidence=0.85,
    )
    record = state.apply_adjudication(adjudication)
    assert record.status == "confirmed"
    assert record.final_adjudication_id == "adj-1"
    assert state.hypotheses["hyp-1"].status == "confirmed"


def test_apply_adjudication_reject_finalizes_hypothesis() -> None:
    state = state_with_debating_hypothesis()
    adjudication = Adjudication(
        adjudication_id="adj-2",
        hypothesis_id="hyp-1",
        round_number=1,
        verdict="reject",
        rationale=["The path is mitigated."],
        accepted_code_evidence_ids=["code-1"],
        accepted_graph_evidence_ids=[],
        missing_proof=[],
        duplicate_of=None,
        confidence=0.3,
    )
    record = state.apply_adjudication(adjudication)
    assert record.status == "rejected"
    assert state.hypotheses["hyp-1"].final_adjudication_id == "adj-2"


def test_apply_adjudication_request_more_evidence_is_non_terminal() -> None:
    state = state_with_debating_hypothesis()
    adjudication = Adjudication(
        adjudication_id="adj-3",
        hypothesis_id="hyp-1",
        round_number=1,
        verdict="request_more_evidence",
        rationale=["Need a concrete sink call."],
        accepted_code_evidence_ids=["code-1"],
        accepted_graph_evidence_ids=[],
        missing_proof=["sink call site"],
        duplicate_of=None,
        confidence=0.4,
    )
    record = state.apply_adjudication(adjudication)
    assert record.status == "debating"
    assert record.final_adjudication_id is None


def test_apply_adjudication_duplicate_marks_duplicate() -> None:
    state = state_with_debating_hypothesis()
    adjudication = Adjudication(
        adjudication_id="adj-5",
        hypothesis_id="hyp-1",
        round_number=1,
        verdict="duplicate",
        rationale=["Same root cause as hyp-0."],
        accepted_code_evidence_ids=["code-1"],
        accepted_graph_evidence_ids=[],
        missing_proof=[],
        duplicate_of="hyp-0",
        confidence=0.7,
    )
    record = state.apply_adjudication(adjudication)
    assert record.status == "duplicate"
    assert adjudication.duplicate_of == "hyp-0"


def test_apply_adjudication_rejects_unknown_evidence_id() -> None:
    state = state_with_debating_hypothesis()
    adjudication = Adjudication(
        adjudication_id="adj-4",
        hypothesis_id="hyp-1",
        round_number=1,
        verdict="confirm",
        rationale=["ok"],
        accepted_code_evidence_ids=["code-missing"],
        accepted_graph_evidence_ids=[],
        missing_proof=[],
        duplicate_of=None,
        confidence=0.9,
    )
    with pytest.raises(ValueError, match="unknown evidence"):
        state.apply_adjudication(adjudication)


def test_repository_profile_requires_profile_evidence() -> None:
    with pytest.raises(ValidationError):
        RepositoryProfile(
            snapshot_id="snap-1",
            model_provider="deepseek",
            model_name="deepseek-v4",
            agent_framework="claude-agent-sdk",
            frontend_roots=["web"],
            backend_roots=["api"],
            model_call_sites=["api/model.py"],
            prompt_assembly_sites=["api/prompt.py"],
            tool_definition_sites=["api/tools.py"],
            retrieval_and_ingestion_sites=["api/rag.py"],
            memory_sites=[],
            authn_authz_sites=["api/auth.py"],
            output_interpretation_sites=["api/parse.py"],
            test_frameworks=["pytest"],
            profile_evidence_ids=[],
            supplied_profile_conflicts=[],
        )


def test_threat_surface_requires_code_evidence() -> None:
    with pytest.raises(ValidationError):
        ThreatSurface(
            surface_id="surf-1",
            kind="prompt_boundary",
            name="RAG prompt boundary",
            entrypoints=["retrieval context"],
            trust_transition="untrusted -> trusted prompt",
            assets=["system prompt"],
            code_evidence_ids=[],
        )


def test_code_evidence_requires_sha256_pattern() -> None:
    with pytest.raises(ValidationError):
        CodeEvidence(
            evidence_id="code-1",
            relative_path="app/main.py",
            line_start=1,
            line_end=2,
            content_sha256="not-a-hash",
            excerpt="x",
            claim="x",
        )


def test_generated_test_draft_validates_fields() -> None:
    draft = GeneratedTestDraft(
        test_id="test-1",
        finding_id="finding-1",
        language="python",
        framework="pytest",
        suggested_target_path="tests/test_prompt_injection.py",
        source="def test_x(): assert True",
        expected_failing_assertion="assert baseline != attack",
        mocked_dependencies=["app.retriever"],
        required_fixtures=["mock_retriever"],
        suggested_run_command="pytest tests/test_prompt_injection.py",
    )
    assert draft.framework == "pytest"


def test_assessment_config_enforces_budget_bounds() -> None:
    with pytest.raises(ValidationError):
        AssessmentConfig(target_repo=Path("/repo"), max_cost_usd=0)
    with pytest.raises(ValidationError):
        AssessmentConfig(target_repo=Path("/repo"), max_agent_calls=2)


def test_assessment_state_persists_team_sessions() -> None:
    state = AssessmentState(
        config=AssessmentConfig(target_repo=Path("/repo")),
        snapshot_id="snap-1",
        team_sessions={"red_team": "session-red"},
    )
    restored = AssessmentState.model_validate(state.model_dump(mode="json"))

    assert restored.team_sessions == {"red_team": "session-red"}


def test_defender_rebuttal_and_red_response_round_bounds() -> None:
    with pytest.raises(ValidationError):
        DefenderRebuttal(
            hypothesis_id="hyp-1",
            round_number=0,
            disposition="refute",
            arguments=["x"],
            new_code_evidence_ids=[],
            unresolved_conditions=[],
        )
    with pytest.raises(ValidationError):
        RedResponse(
            hypothesis_id="hyp-1",
            round_number=0,
            disposition="stand",
            reasoning=["x"],
            revised_hypothesis=None,
            new_code_evidence_ids=[],
            new_graph_evidence_ids=[],
        )
