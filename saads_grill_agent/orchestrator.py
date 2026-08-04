"""Evidence-driven state machine for adversarial repository assessments."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from saads_grill_agent.contracts import (
    Adjudication,
    AssessmentConfig,
    AssessmentState,
    DefenderRebuttal,
    Finding,
    GeneratedTestDraft,
    HypothesisRecord,
    RedResponse,
    RepositoryProfile,
    ThreatSurface,
    VulnerabilityHypothesis,
)
from saads_grill_agent.repository import RepositoryEvidenceStore
from saads_grill_agent.teams import (
    HypothesisBatch,
    RebuttalBatch,
    RedResponseBatch,
    TeamBackend,
    TeamTurnAudits,
)


class AssessmentLedger(Protocol):
    """The small persistence surface needed before the full ledger exists."""

    def checkpoint(self, state: AssessmentState) -> None: ...

    def append_event(self, event: str, **details: Any) -> None: ...


class ProfileResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: RepositoryProfile
    threat_surfaces: list[ThreatSurface]


class _ResourceLimit(RuntimeError):
    pass


class AssessmentOrchestrator:
    """Run profile, discovery, debate and test-draft phases in order."""

    def __init__(
        self,
        *,
        backend: TeamBackend,
        evidence_store: RepositoryEvidenceStore,
        ledger: AssessmentLedger,
        security_graph: Any | None = None,
    ) -> None:
        self._backend = backend
        self._store = evidence_store
        self._ledger = ledger
        self._security_graph = security_graph
        self._sessions: dict[str, str] = {}

    async def run(self, config: AssessmentConfig) -> AssessmentState:
        state = AssessmentState(config=config, snapshot_id=self._store.snapshot_id)
        return await self._continue(state)

    async def resume(self, state: AssessmentState) -> AssessmentState:
        if state.snapshot_id != self._store.snapshot_id:
            raise ValueError("repository snapshot does not match the assessment state")
        if state.phase not in {"interrupted", "intake", "profiling", "discovery", "debating"}:
            return state
        return await self._continue(state)

    async def _continue(self, state: AssessmentState) -> AssessmentState:
        try:
            if state.profile is None:
                state.phase = "profiling"
                profile = await self._turn(
                    state, "code_team", "Profile repository attack surfaces.", ProfileResult
                )
                self._register_profile_evidence(state, profile)
                if profile.profile.snapshot_id != state.snapshot_id:
                    raise ValueError("profile snapshot does not match the repository snapshot")
                if len(profile.threat_surfaces) > state.config.max_threat_surfaces:
                    raise _ResourceLimit("max_threat_surfaces")
                state.profile = profile.profile
                state.threat_surfaces = profile.threat_surfaces
                self._checkpoint(state)

            state.phase = "discovery"
            await self._discover(state)
            if state.phase == "interrupted":
                return state
            state.phase = "generating_tests"
            await self._generate_test_drafts(state)
            state.phase = "complete"
            self._checkpoint(state)
            return state
        except _ResourceLimit as exc:
            return await self._interrupt(state, str(exc))

    async def _discover(self, state: AssessmentState) -> None:
        while state.discovery.consecutive_empty_sweeps < 2:
            batch = await self._turn(
                state, "red_team", "Discover one or more grounded vulnerability hypotheses.",
                HypothesisBatch,
            )
            added = self._add_hypotheses(state, batch.hypotheses)
            if not added:
                state.discovery.consecutive_empty_sweeps += 1
                self._checkpoint(state)
                continue
            state.discovery.consecutive_empty_sweeps = 0
            for hypothesis_id in added:
                await self._debate(state, hypothesis_id)
                if state.phase == "interrupted":
                    return

    def _add_hypotheses(
        self, state: AssessmentState, hypotheses: list[VulnerabilityHypothesis]
    ) -> list[str]:
        added: list[str] = []
        known_keys = {
            self._hypothesis_key(record.hypothesis) for record in state.hypotheses.values()
        }
        for hypothesis in hypotheses:
            self._register_hypothesis_evidence(state, hypothesis)
            key = self._hypothesis_key(hypothesis)
            if key in known_keys:
                self._event("hypothesis_duplicate", hypothesis_id=hypothesis.hypothesis_id)
                continue
            if len(state.hypotheses) >= state.config.max_hypotheses:
                raise _ResourceLimit("max_hypotheses")
            state.hypotheses[hypothesis.hypothesis_id] = HypothesisRecord(
                hypothesis=hypothesis, status="debating", final_adjudication_id=None
            )
            known_keys.add(key)
            added.append(hypothesis.hypothesis_id)
        return added

    async def _debate(self, state: AssessmentState, hypothesis_id: str) -> None:
        unchanged_rounds = 0
        for round_number in range(1, state.config.max_rounds_per_hypothesis + 1):
            record = state.hypotheses[hypothesis_id]
            if record.status != "debating":
                return
            before = set(state.evidence_ids)
            rebuttals = await self._turn(
                state, "code_team",
                f"Falsify hypothesis {hypothesis_id} with concrete repository evidence.",
                RebuttalBatch,
            )
            rebuttal = self._one_for_hypothesis(rebuttals.rebuttals, hypothesis_id)
            if rebuttal is not None:
                self._register_rebuttal_evidence(state, rebuttal)
            responses = await self._turn(
                state, "red_team",
                f"Respond to the rebuttal for hypothesis {hypothesis_id}.",
                RedResponseBatch,
            )
            response = self._one_for_hypothesis(responses.responses, hypothesis_id)
            if response is not None:
                self._register_response_evidence(state, response)
                if response.revised_hypothesis is not None:
                    self._register_hypothesis_evidence(state, response.revised_hypothesis)
                    state.hypotheses[hypothesis_id] = HypothesisRecord(
                        hypothesis=response.revised_hypothesis,
                        status="debating",
                        final_adjudication_id=None,
                    )
                if response.disposition == "withdraw":
                    self._withdraw(state, hypothesis_id, round_number)
                    return
            unchanged_rounds = unchanged_rounds + 1 if set(state.evidence_ids) == before else 0
            adjudication = await self._turn(
                state, "judge",
                f"Adjudicate hypothesis {hypothesis_id}; return a terminal verdict at final round.",
                Adjudication,
            )
            if adjudication.hypothesis_id != hypothesis_id:
                raise ValueError("judge adjudicated a different hypothesis")
            if (
                round_number == state.config.max_rounds_per_hypothesis
                or unchanged_rounds >= 2
            ) and adjudication.verdict == "request_more_evidence":
                raise ValueError("judge must issue a terminal verdict at convergence")
            state.apply_adjudication(adjudication)
            if adjudication.verdict == "confirm":
                self._add_finding(state, adjudication)
            self._checkpoint(state)
            if state.hypotheses[hypothesis_id].status != "debating":
                return

    async def _generate_test_drafts(self, state: AssessmentState) -> None:
        for finding in state.findings:
            draft = await self._turn(
                state, "red_team",
                f"Generate a non-executing regression test draft for {finding.finding_id}.",
                GeneratedTestDraft,
            )
            if draft.finding_id != finding.finding_id:
                raise ValueError("test draft does not match its finding")
            finding.generated_test_ids.append(draft.test_id)
            self._checkpoint(state)

    async def _turn(
        self,
        state: AssessmentState,
        role: str,
        prompt: str,
        output_model: type[BaseModel],
        *,
        enforce_limits: bool = True,
    ) -> Any:
        if enforce_limits and state.agent_calls_used >= state.config.max_agent_calls:
            raise _ResourceLimit("max_agent_calls")
        result = await self._backend.run_turn(
            role=role,
            prompt=prompt,
            output_model=output_model,
            session_id=self._sessions.get(role),
            audits=TeamTurnAudits(),
        )
        self._sessions[role] = result.session_id
        state.agent_calls_used += 1
        if result.total_cost_usd is None:
            self._event("missing_cost_metadata", role=role)
            raise _ResourceLimit("missing_cost_metadata")
        state.cost_usd_used += result.total_cost_usd
        if enforce_limits and state.cost_usd_used >= state.config.max_cost_usd:
            raise _ResourceLimit("max_cost_usd")
        return result.output

    async def _interrupt(self, state: AssessmentState, reason: str) -> AssessmentState:
        state.phase = "interrupted"
        self._event("resource_cap_reached", reason=reason)
        await self._finalize_active_hypotheses(state)
        self._checkpoint(state)
        return state

    async def _finalize_active_hypotheses(self, state: AssessmentState) -> None:
        """Ask the judge for a terminal decision after resource exhaustion."""
        for hypothesis_id, record in list(state.hypotheses.items()):
            if record.status != "debating":
                continue
            try:
                adjudication = await self._turn(
                    state,
                    "judge",
                    f"Resource limit reached. Issue a terminal judgment for {hypothesis_id}.",
                    Adjudication,
                    enforce_limits=False,
                )
                if (
                    adjudication.hypothesis_id != hypothesis_id
                    or adjudication.verdict == "request_more_evidence"
                ):
                    raise ValueError("forced final judgment was not terminal")
                state.apply_adjudication(adjudication)
                if adjudication.verdict == "confirm":
                    self._add_finding(state, adjudication)
            except Exception as exc:  # preserve the checkpointed partial assessment
                self._event("forced_finalization_failed", hypothesis_id=hypothesis_id, error=str(exc))

    def _withdraw(self, state: AssessmentState, hypothesis_id: str, round_number: int) -> None:
        record = state.hypotheses[hypothesis_id]
        evidence_ids = record.hypothesis.code_evidence_ids + record.hypothesis.graph_evidence_ids
        adjudication = Adjudication(
            adjudication_id=f"withdraw-{hypothesis_id}-{round_number}",
            hypothesis_id=hypothesis_id,
            round_number=round_number,
            verdict="reject",
            rationale=["Red team withdrew the claim."],
            accepted_code_evidence_ids=record.hypothesis.code_evidence_ids[:1],
            accepted_graph_evidence_ids=[] if record.hypothesis.code_evidence_ids else evidence_ids[:1],
            missing_proof=[],
            duplicate_of=None,
            confidence=0.0,
        )
        state.apply_adjudication(adjudication)
        self._checkpoint(state)

    def _register_profile_evidence(self, state: AssessmentState, profile: ProfileResult) -> None:
        state.register_evidence(*profile.profile.profile_evidence_ids)
        for surface in profile.threat_surfaces:
            state.register_evidence(*surface.code_evidence_ids)

    @staticmethod
    def _register_hypothesis_evidence(
        state: AssessmentState, hypothesis: VulnerabilityHypothesis
    ) -> None:
        state.register_evidence(*hypothesis.code_evidence_ids, *hypothesis.graph_evidence_ids)

    @staticmethod
    def _register_rebuttal_evidence(state: AssessmentState, rebuttal: DefenderRebuttal) -> None:
        state.register_evidence(*rebuttal.new_code_evidence_ids)

    @staticmethod
    def _register_response_evidence(state: AssessmentState, response: RedResponse) -> None:
        state.register_evidence(*response.new_code_evidence_ids, *response.new_graph_evidence_ids)

    @staticmethod
    def _one_for_hypothesis(items: list[Any], hypothesis_id: str) -> Any | None:
        return next((item for item in items if item.hypothesis_id == hypothesis_id), None)

    @staticmethod
    def _hypothesis_key(hypothesis: VulnerabilityHypothesis) -> str:
        source = hypothesis.attack_path[0]
        sink = hypothesis.attack_path[-1]
        normalized = "\0".join(
            " ".join(value.lower().split())
            for value in (hypothesis.surface_id, hypothesis.root_cause, source, sink)
        )
        return sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _add_finding(state: AssessmentState, adjudication: Adjudication) -> None:
        hypothesis = state.hypotheses[adjudication.hypothesis_id].hypothesis
        if any(finding.hypothesis_id == hypothesis.hypothesis_id for finding in state.findings):
            return
        confidence = (
            "high" if adjudication.confidence >= 0.8
            else "medium" if adjudication.confidence >= 0.5
            else "low"
        )
        state.findings.append(Finding(
            finding_id=f"finding-{hypothesis.hypothesis_id}",
            hypothesis_id=hypothesis.hypothesis_id,
            severity="medium",
            confidence=confidence,
            root_cause=hypothesis.root_cause,
            attack_path=hypothesis.attack_path,
            impact=hypothesis.impact,
            preconditions=hypothesis.preconditions,
            code_evidence_ids=adjudication.accepted_code_evidence_ids,
            graph_evidence_ids=adjudication.accepted_graph_evidence_ids,
            remediation="Validate untrusted input before it crosses this trust boundary.",
        ))

    def _checkpoint(self, state: AssessmentState) -> None:
        self._ledger.checkpoint(state)

    def _event(self, event: str, **details: Any) -> None:
        self._ledger.append_event(event, **details)
