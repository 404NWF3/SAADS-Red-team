from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from saads_grill_agent.contracts import (
    Adjudication,
    AssessmentConfig,
    DefenderRebuttal,
    GeneratedTestDraft,
    RedResponse,
    RepositoryProfile,
    ThreatSurface,
    VulnerabilityHypothesis,
)
from saads_grill_agent.orchestrator import (
    AssessmentOrchestrator,
    ProfileResult,
    derive_hypothesis_id,
)
from saads_grill_agent.repository import RepositoryEvidenceStore
from saads_grill_agent.teams import (
    HypothesisBatch,
    RebuttalBatch,
    RedResponseBatch,
    TeamTurnAudits,
    TeamTurnResult,
)


@dataclass
class FakeLedger:
    checkpoints: list[Any] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    _issued_evidence_ids: list[str] = field(default_factory=list)

    def checkpoint(self, state: Any) -> None:
        self.checkpoints.append(state.model_copy(deep=True))

    def append_event(self, event: str, **details: Any) -> None:
        self.events.append({"event": event, **details})

    def record_issued_evidence(self, *evidence_ids: str) -> None:
        for evidence_id in evidence_ids:
            if evidence_id not in self._issued_evidence_ids:
                self._issued_evidence_ids.append(evidence_id)

    def list_issued_evidence(self) -> list[str]:
        return list(self._issued_evidence_ids)


class ScriptedTeamBackend:
    def __init__(self, outputs: list[Any], costs: list[float | None] | None = None) -> None:
        self.outputs = list(outputs)
        self.costs = costs or [0.01] * len(outputs)
        self.role_order: list[str] = []
        self.session_ids: list[str | None] = []

    async def run_turn(
        self,
        *,
        role: str,
        prompt: str,
        output_model: type[Any],
        session_id: str | None,
        audits: TeamTurnAudits,
    ) -> TeamTurnResult:
        self.role_order.append(role)
        self.session_ids.append(session_id)
        output = self.outputs.pop(0)
        return TeamTurnResult(
            output=output_model.model_validate(output),
            session_id=f"{role}-{len(self.role_order)}",
            total_cost_usd=self.costs.pop(0),
            usage=None,
        )


def config(repo: Path, **overrides: Any) -> AssessmentConfig:
    return AssessmentConfig(target_repo=repo, **overrides)


def profile_result(snapshot_id: str, surfaces: int = 1) -> ProfileResult:
    evidence_ids = [f"code-profile-{index}" for index in range(surfaces)]
    profile = RepositoryProfile(
        snapshot_id=snapshot_id,
        model_provider="test",
        model_name="test-model",
        agent_framework="test-framework",
        frontend_roots=["web"],
        backend_roots=["app"],
        model_call_sites=["app/model.py"],
        prompt_assembly_sites=["app/prompt.py"],
        tool_definition_sites=["app/tools.py"],
        retrieval_and_ingestion_sites=["app/rag.py"],
        memory_sites=[],
        authn_authz_sites=["app/auth.py"],
        output_interpretation_sites=["app/output.py"],
        test_frameworks=["pytest"],
        profile_evidence_ids=evidence_ids,
        supplied_profile_conflicts=[],
    )
    threat_surfaces = [
        ThreatSurface(
            surface_id=f"surface-{index}",
            kind="prompt_boundary",
            name=f"Prompt boundary {index}",
            entrypoints=["request"],
            trust_transition="untrusted input reaches prompt",
            assets=["system prompt"],
            code_evidence_ids=[evidence_ids[index]],
        )
        for index in range(surfaces)
    ]
    return ProfileResult(profile=profile, threat_surfaces=threat_surfaces)


def hypothesis(
    hypothesis_id: str = "hyp-pi-1",
    surface_id: str = "surface-0",
    root_cause: str = "Untrusted context reaches the model prompt",
    attack_path: list[str] | None = None,
) -> VulnerabilityHypothesis:
    result = VulnerabilityHypothesis(
        hypothesis_id=hypothesis_id,  # ignored by the orchestrator
        surface_id=surface_id,
        title="Prompt injection",
        root_cause=root_cause,
        attack_path=attack_path or ["request input", "model invocation"],
        impact="Instruction hijack",
        preconditions=["attacker controls input"],
        code_evidence_ids=["code-hypothesis"],
        graph_evidence_ids=[],
    )
    return result.model_copy(update={"hypothesis_id": derive_hypothesis_id(result)})


def rebuttal(hypothesis_id: str | None = None, evidence: list[str] | None = None) -> RebuttalBatch:
    hypothesis_id = hypothesis_id or hypothesis().hypothesis_id
    return RebuttalBatch(rebuttals=[DefenderRebuttal(
        hypothesis_id=hypothesis_id,
        round_number=1,
        disposition="mitigated",
        arguments=["A partial filter exists."],
        new_code_evidence_ids=["code-filter"] if evidence is None else evidence,
        unresolved_conditions=["Bypass behavior"],
    )])


def red_response(
    hypothesis_id: str | None = None,
    disposition: str = "stand",
    evidence: list[str] | None = None,
) -> RedResponseBatch:
    hypothesis_id = hypothesis_id or hypothesis().hypothesis_id
    return RedResponseBatch(responses=[RedResponse(
        hypothesis_id=hypothesis_id,
        round_number=1,
        disposition=disposition,  # type: ignore[arg-type]
        reasoning=["The filter is bypassable."],
        revised_hypothesis=None,
        new_code_evidence_ids=["code-bypass"] if evidence is None else evidence,
        new_graph_evidence_ids=[],
    )])


def adjudication(
    verdict: str = "confirm",
    hypothesis_id: str | None = None,
    round_number: int = 1,
    accepted_evidence: str = "code-bypass",
) -> Adjudication:
    hypothesis_id = hypothesis_id or hypothesis().hypothesis_id
    return Adjudication(
        adjudication_id=f"adj-{hypothesis_id}-{round_number}",
        hypothesis_id=hypothesis_id,
        round_number=round_number,
        verdict=verdict,  # type: ignore[arg-type]
        rationale=["The path is reachable."],
        accepted_code_evidence_ids=[accepted_evidence],
        accepted_graph_evidence_ids=[],
        missing_proof=[],
        duplicate_of=None,
        confidence=0.9,
    )


def generated_test_draft(finding_id: str | None = None) -> GeneratedTestDraft:
    finding_id = finding_id or f"finding-{hypothesis().hypothesis_id}"
    return GeneratedTestDraft(
        test_id="test-pi-1",
        finding_id=finding_id,
        language="python",
        framework="pytest",
        suggested_target_path="tests/test_prompt.py",
        source="def test_prompt_injection(): assert False",
        expected_failing_assertion="assert output != injected_instruction",
        suggested_run_command="pytest tests/test_prompt.py",
    )


def default_ledger() -> FakeLedger:
    ledger = FakeLedger()
    ledger.record_issued_evidence(
        *[f"code-profile-{index}" for index in range(50)],
        "code-hypothesis", "code-filter", "code-bypass",
        *[f"code-round-{index}" for index in range(1, 5)],
    )
    return ledger


def orchestrator(backend: ScriptedTeamBackend, repo: Path, ledger: FakeLedger | None = None) -> AssessmentOrchestrator:
    return AssessmentOrchestrator(
        backend=backend,
        evidence_store=RepositoryEvidenceStore.open(repo),
        ledger=ledger or default_ledger(),
    )


def test_debate_confirms_only_after_rebuttal_red_response_and_judgment(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id),
        HypothesisBatch(hypotheses=[hypothesis()]),
        rebuttal(),
        red_response(),
        adjudication(),
        HypothesisBatch(hypotheses=[]),
        HypothesisBatch(hypotheses=[]),
        generated_test_draft(),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    hypothesis_id = hypothesis().hypothesis_id
    assert [finding.hypothesis_id for finding in state.findings] == [hypothesis_id]
    assert state.hypotheses[hypothesis_id].status == "confirmed"
    finding = state.findings[0]
    assert finding.judge_rationale == ["The path is reachable."]
    assert finding.strongest_rebuttal == ["A partial filter exists."]
    assert finding.rebuttal_failure_reason == "The filter is bypassable."
    assert finding.confidence_score == 0.9
    assert finding.confidence == "high"
    assert state.discovery.consecutive_empty_sweeps == 2
    assert backend.role_order == [
        "code_team", "red_team", "code_team", "red_team", "judge",
        "red_team", "red_team", "red_team",
    ]


def test_red_withdrawal_is_finalized_by_a_judge_turn(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[hypothesis()]),
        rebuttal(), red_response(disposition="withdraw"), adjudication("reject"),
        HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert state.hypotheses[hypothesis().hypothesis_id].status == "rejected"
    assert "judge" in backend.role_order


def test_judge_rejection_creates_no_finding(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[hypothesis()]),
        rebuttal(), red_response(), adjudication("reject"),
        HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert state.hypotheses[hypothesis().hypothesis_id].status == "rejected"
    assert state.findings == []


def test_model_cited_evidence_must_have_been_issued(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    ledger = FakeLedger()
    ledger.record_issued_evidence("code-profile-0")
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id),
        HypothesisBatch(hypotheses=[hypothesis()]),
    ])

    with pytest.raises(ValueError, match="unknown evidence"):
        asyncio.run(orchestrator(backend, tmp_path, ledger).run(config(tmp_path)))


def test_duplicate_hypothesis_is_not_debated_twice(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    first = hypothesis("model-wording-one")
    duplicate = hypothesis("model-wording-two")
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[first, duplicate]),
        rebuttal(first.hypothesis_id), red_response(first.hypothesis_id),
        adjudication(hypothesis_id=first.hypothesis_id),
        HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
        generated_test_draft(f"finding-{first.hypothesis_id}"),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert len(state.hypotheses) == 1
    assert backend.role_order.count("code_team") == 2


def test_orchestrator_replaces_model_hypothesis_id_with_canonical_id(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    expected = hypothesis().hypothesis_id
    model_hypothesis = hypothesis().model_copy(update={"hypothesis_id": "model-selected-id"})
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[model_hypothesis]),
        rebuttal(expected), red_response(expected), adjudication(hypothesis_id=expected),
        HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
        generated_test_draft(f"finding-{expected}"),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert list(state.hypotheses) == [expected]
    assert "model-selected-id" not in state.hypotheses


def test_refined_hypothesis_replaces_its_model_selected_id(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    initial = hypothesis()
    revised = hypothesis(root_cause="Refined root cause").model_copy(
        update={"hypothesis_id": "nonsense-model-id"}
    )
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[initial]),
        rebuttal(initial.hypothesis_id),
        RedResponseBatch(responses=[RedResponse(
            hypothesis_id=initial.hypothesis_id,
            round_number=1,
            disposition="refine",
            reasoning=["The root cause is more specific."],
            revised_hypothesis=revised,
            new_code_evidence_ids=["code-bypass"],
            new_graph_evidence_ids=[],
        )]),
        adjudication("reject", hypothesis_id=initial.hypothesis_id),
        HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert state.hypotheses[initial.hypothesis_id].hypothesis.hypothesis_id == derive_hypothesis_id(revised)
    assert state.hypotheses[initial.hypothesis_id].hypothesis.hypothesis_id != "nonsense-model-id"


def test_fourth_round_forces_a_terminal_judgment(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    outputs: list[Any] = [profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[hypothesis()])]
    for round_number in range(1, 5):
        evidence_id = f"code-round-{round_number}"
        outputs.extend([
            RebuttalBatch(rebuttals=[rebuttal().rebuttals[0].model_copy(update={
                "round_number": round_number, "new_code_evidence_ids": [evidence_id],
            })]),
            RedResponseBatch(responses=[red_response().responses[0].model_copy(update={"round_number": round_number})]),
            adjudication(
                "request_more_evidence" if round_number < 4 else "reject",
                round_number=round_number,
            ),
        ])
    outputs.extend([HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[])])
    backend = ScriptedTeamBackend(outputs)

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert state.hypotheses[hypothesis().hypothesis_id].status == "rejected"
    assert backend.role_order.count("judge") == 4


def test_two_rounds_without_new_evidence_force_final_judgment(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    first = adjudication("request_more_evidence", accepted_evidence="code-hypothesis")
    second = adjudication("reject", round_number=2, accepted_evidence="code-hypothesis")
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), HypothesisBatch(hypotheses=[hypothesis()]),
        rebuttal(evidence=[]), red_response(evidence=[]), first,
        RebuttalBatch(rebuttals=[rebuttal().rebuttals[0].model_copy(update={"round_number": 2, "new_code_evidence_ids": []})]),
        RedResponseBatch(responses=[red_response().responses[0].model_copy(update={"round_number": 2, "new_code_evidence_ids": []})]),
        second, HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
    ])

    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path)))

    assert state.hypotheses[hypothesis().hypothesis_id].status == "rejected"
    assert backend.role_order.count("judge") == 2


@pytest.mark.parametrize(
    ("limit_name", "limit", "profile_surfaces", "hypotheses", "costs"),
    [
        ("max_threat_surfaces", 20, 21, [], None),
        ("max_hypotheses", 40, 1, [
            hypothesis(f"hyp-{index}", root_cause=f"Root cause {index}") for index in range(41)
        ], None),
        ("max_agent_calls", 5, 1, [], None),
        ("max_cost_usd", 25.0, 1, [], [30.0]),
    ],
)
def test_resource_caps_checkpoint_and_interrupt(
    tmp_path: Path,
    limit_name: str,
    limit: int | float,
    profile_surfaces: int,
    hypotheses: list[VulnerabilityHypothesis],
    costs: list[float | None] | None,
) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    ledger = default_ledger()
    outputs: list[Any] = [
        profile_result(store.snapshot_id, profile_surfaces),
        HypothesisBatch(hypotheses=hypotheses),
    ]
    if limit_name == "max_agent_calls":
        outputs = [
            profile_result(store.snapshot_id),
            HypothesisBatch(hypotheses=[hypothesis()]),
            rebuttal(),
            red_response(),
            adjudication("request_more_evidence"),
        ]
    if limit_name == "max_hypotheses":
        outputs.extend([
            adjudication(
                "reject",
                hypothesis_id=hypotheses[index].hypothesis_id,
                accepted_evidence="code-hypothesis",
            )
            for index in range(40)
        ])
    backend = ScriptedTeamBackend(
        outputs,
        costs=costs,
    )

    state = asyncio.run(orchestrator(backend, tmp_path, ledger).run(config(tmp_path, **{limit_name: limit})))

    assert state.phase == "interrupted"
    assert ledger.checkpoints
    assert any(event["event"] == "resource_cap_reached" for event in ledger.events)
    if limit_name == "max_agent_calls":
        assert backend.role_order == ["code_team", "red_team", "code_team", "red_team", "judge"]
        assert state.hypotheses[hypothesis().hypothesis_id].status == "debating"
    if limit_name == "max_hypotheses":
        assert backend.role_order.count("judge") == 40
        assert all(record.status == "rejected" for record in state.hypotheses.values())


def test_missing_cost_metadata_interrupts_and_checkpoints(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    ledger = default_ledger()
    backend = ScriptedTeamBackend([profile_result(store.snapshot_id)], costs=[None])

    state = asyncio.run(orchestrator(backend, tmp_path, ledger).run(config(tmp_path)))

    assert state.phase == "interrupted"
    assert any(event["event"] == "missing_cost_metadata" for event in ledger.events)


def test_resume_continues_an_interrupted_run(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    backend = ScriptedTeamBackend([
        profile_result(store.snapshot_id), profile_result(store.snapshot_id),
        HypothesisBatch(hypotheses=[]), HypothesisBatch(hypotheses=[]),
    ])
    subject = orchestrator(backend, tmp_path)
    state = asyncio.run(subject.run(config(tmp_path, max_cost_usd=0.01)))
    assert state.phase == "interrupted"
    state.cost_usd_used = 0.0
    state.agent_calls_used = 0
    state.config.max_cost_usd = 25.0

    resumed = asyncio.run(orchestrator(backend, tmp_path).resume(state))

    assert resumed.phase == "complete"
    assert backend.session_ids[1] == "code_team-1"


def test_resume_rejects_repository_snapshot_mismatch(tmp_path: Path) -> None:
    store = RepositoryEvidenceStore.open(tmp_path)
    backend = ScriptedTeamBackend([profile_result(store.snapshot_id)])
    state = asyncio.run(orchestrator(backend, tmp_path).run(config(tmp_path, max_cost_usd=0.01)))
    (tmp_path / "changed.py").write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="snapshot"):
        asyncio.run(orchestrator(ScriptedTeamBackend([]), tmp_path).resume(state))
