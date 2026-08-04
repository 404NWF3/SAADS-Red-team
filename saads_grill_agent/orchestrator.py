"""Evidence-driven state machine for adversarial repository assessments."""

from __future__ import annotations

from hashlib import sha256
from collections.abc import Callable
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
from saads_grill_agent.report import confidence_level
from saads_grill_agent.repository import RepositoryEvidenceStore
from saads_grill_agent.teams import (
    HypothesisBatch,
    RebuttalBatch,
    RedResponseBatch,
    TeamBackend,
    TeamTurnAudits,
)


class AssessmentLedger(Protocol):
    """Persistence surface; Task 6 records IDs when MCP tools issue evidence."""

    def checkpoint(self, state: AssessmentState) -> None: ...

    def append_event(self, event: str, **details: Any) -> None: ...

    def record_issued_evidence(self, *evidence_ids: str) -> None: ...

    def list_issued_evidence(self) -> list[str]: ...


class ProfileResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: RepositoryProfile
    threat_surfaces: list[ThreatSurface]


class _ResourceLimit(RuntimeError):
    pass


def derive_hypothesis_id(hypothesis: VulnerabilityHypothesis) -> str:
    """Derive the ledger identity from the canonical source-to-sink tuple."""
    source = hypothesis.attack_path[0]
    sink = hypothesis.attack_path[-1]
    normalized = "\0".join(
        " ".join(value.lower().split())
        for value in (hypothesis.surface_id, hypothesis.root_cause, source, sink)
    )
    return "hyp-" + sha256(normalized.encode("utf-8")).hexdigest()[:16]


class AssessmentOrchestrator:
    """Run profile, discovery, debate and test-draft phases in order."""

    def __init__(
        self,
        *,
        backend: TeamBackend,
        evidence_store: RepositoryEvidenceStore,
        ledger: AssessmentLedger,
        security_graph: Any | None = None,
        publish_test_draft: Callable[
            [GeneratedTestDraft, Finding, AssessmentState], None
        ]
        | None = None,
        code_audit: list[Any] | None = None,
        graph_audit: list[Any] | None = None,
    ) -> None:
        self._backend = backend
        self._store = evidence_store
        self._ledger = ledger
        self._security_graph = security_graph
        self._publish_test_draft = publish_test_draft
        self._code_audit = code_audit if code_audit is not None else []
        self._graph_audit = graph_audit if graph_audit is not None else []

    async def run(self, config: AssessmentConfig) -> AssessmentState:
        state = AssessmentState(config=config, snapshot_id=self._store.snapshot_id)
        state.register_evidence(*self._ledger.list_issued_evidence())
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
                    state,
                    "code_team",
                    (
                        "Profile repository attack surfaces and return ProfileResult ASAP. "
                        "Do not spawn subagents. Use only repository MCP tools: "
                        "list_repository, then a few search_repository / "
                        "read_repository_snippet calls for model, prompt, tool, RAG, "
                        "and auth seams. Prefer signed snippets over exhaustive "
                        "exploration. You MUST cite only evidence_id values returned by "
                        "read_repository_snippet; never invent IDs such as ev-* "
                        "and never put file paths in evidence_id fields."
                    ),
                    ProfileResult,
                    enable_subagents=False,
                )
                profile = self._normalize_profile_evidence(state, profile)
                self._require_profile_evidence(state, profile)
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
            key = self._hypothesis_key(hypothesis)
            if key in known_keys:
                self._event("hypothesis_duplicate", hypothesis_id=hypothesis.hypothesis_id)
                continue
            if len(state.hypotheses) >= state.config.max_hypotheses:
                raise _ResourceLimit("max_hypotheses")
            canonical_id = derive_hypothesis_id(hypothesis)
            code_ids = [
                evidence_id
                for evidence_id in hypothesis.code_evidence_ids
                if evidence_id in state.evidence_ids
            ]
            graph_ids = [
                evidence_id
                for evidence_id in hypothesis.graph_evidence_ids
                if evidence_id in state.evidence_ids
            ]
            if not code_ids and not graph_ids:
                # Drop model-invented citations rather than aborting discovery.
                continue
            canonical = hypothesis.model_copy(
                update={
                    "hypothesis_id": canonical_id,
                    "code_evidence_ids": code_ids,
                    "graph_evidence_ids": graph_ids,
                }
            )
            state.hypotheses[canonical_id] = HypothesisRecord(
                hypothesis=canonical, status="debating", final_adjudication_id=None
            )
            known_keys.add(key)
            added.append(canonical_id)
        return added

    async def _debate(self, state: AssessmentState, hypothesis_id: str) -> None:
        unchanged_rounds = 0
        thread_evidence = set(
            state.hypotheses[hypothesis_id].hypothesis.code_evidence_ids
            + state.hypotheses[hypothesis_id].hypothesis.graph_evidence_ids
        )
        last_rebuttal: DefenderRebuttal | None = None
        last_response: RedResponse | None = None
        for round_number in range(1, state.config.max_rounds_per_hypothesis + 1):
            record = state.hypotheses[hypothesis_id]
            if record.status != "debating":
                return
            before = set(thread_evidence)
            rebuttals = await self._turn(
                state, "code_team",
                f"Falsify hypothesis {hypothesis_id} with concrete repository evidence.",
                RebuttalBatch,
            )
            rebuttal = self._one_for_hypothesis(rebuttals.rebuttals, hypothesis_id)
            if rebuttal is not None:
                last_rebuttal = rebuttal
                self._require_issued(state, *rebuttal.new_code_evidence_ids)
                thread_evidence.update(rebuttal.new_code_evidence_ids)
            responses = await self._turn(
                state, "red_team",
                f"Respond to the rebuttal for hypothesis {hypothesis_id}.",
                RedResponseBatch,
            )
            response = self._one_for_hypothesis(responses.responses, hypothesis_id)
            if response is not None:
                last_response = response
                self._require_issued(
                    state, *response.new_code_evidence_ids, *response.new_graph_evidence_ids
                )
                thread_evidence.update(
                    response.new_code_evidence_ids + response.new_graph_evidence_ids
                )
                if response.revised_hypothesis is not None:
                    self._require_issued(
                        state,
                        *response.revised_hypothesis.code_evidence_ids,
                        *response.revised_hypothesis.graph_evidence_ids,
                    )
                    # The thread key remains stable so the current judge turn can
                    # adjudicate it; the stored hypothesis always has a canonical ID.
                    revised = response.revised_hypothesis.model_copy(
                        update={
                            "hypothesis_id": derive_hypothesis_id(
                                response.revised_hypothesis
                            )
                        }
                    )
                    state.hypotheses[hypothesis_id] = HypothesisRecord(
                        hypothesis=revised,
                        status="debating",
                        final_adjudication_id=None,
                    )
            unchanged_rounds = unchanged_rounds + 1 if thread_evidence == before else 0
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
                self._add_finding(
                    state,
                    adjudication,
                    rebuttal=last_rebuttal,
                    red_response=last_response,
                )
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
            if self._publish_test_draft is not None:
                self._publish_test_draft(draft, finding, state)
            self._checkpoint(state)

    async def _turn(
        self,
        state: AssessmentState,
        role: str,
        prompt: str,
        output_model: type[BaseModel],
        *,
        enable_subagents: bool = True,
    ) -> Any:
        if state.agent_calls_used >= state.config.max_agent_calls:
            raise _ResourceLimit("max_agent_calls")
        result = await self._backend.run_turn(
            role=role,
            prompt=prompt,
            output_model=output_model,
            session_id=state.team_sessions.get(role),
            audits=TeamTurnAudits(),
            enable_subagents=enable_subagents,
        )
        self._sync_issued_evidence(state)
        state.team_sessions[role] = result.session_id
        state.agent_calls_used += 1
        if result.total_cost_usd is None:
            self._event("missing_cost_metadata", role=role)
            raise _ResourceLimit("missing_cost_metadata")
        state.cost_usd_used += result.total_cost_usd
        if state.cost_usd_used >= state.config.max_cost_usd:
            raise _ResourceLimit("max_cost_usd")
        return result.output

    def _sync_issued_evidence(self, state: AssessmentState) -> None:
        """Register evidence IDs issued by MCP tools during the latest turn."""
        issued: list[str] = []
        for item in self._code_audit:
            evidence_id = getattr(item, "evidence_id", None)
            if isinstance(evidence_id, str) and evidence_id:
                issued.append(evidence_id)
        for item in self._graph_audit:
            evidence_id = getattr(item, "evidence_id", None)
            if isinstance(evidence_id, str) and evidence_id:
                issued.append(evidence_id)
        if not issued:
            return
        self._ledger.record_issued_evidence(*issued)
        state.register_evidence(*issued)

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
            if (
                state.agent_calls_used >= state.config.max_agent_calls
                or state.cost_usd_used >= state.config.max_cost_usd
            ):
                return
            try:
                adjudication = await self._turn(
                    state,
                    "judge",
                    f"Resource limit reached. Issue a terminal judgment for {hypothesis_id}.",
                    Adjudication,
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

    def _normalize_profile_evidence(
        self, state: AssessmentState, profile: ProfileResult
    ) -> ProfileResult:
        """Bind profile citations to MCP-issued IDs; drop invented paths/IDs."""
        issued = list(state.evidence_ids)
        if not issued:
            raise ValueError(
                "profiling produced no signed repository evidence; "
                "call read_repository_snippet before citing evidence_id values"
            )

        def keep(ids: list[str]) -> list[str]:
            kept = [evidence_id for evidence_id in ids if evidence_id in state.evidence_ids]
            return kept or [issued[0]]

        normalized_profile = profile.profile.model_copy(
            update={
                "snapshot_id": state.snapshot_id,
                "profile_evidence_ids": keep(profile.profile.profile_evidence_ids),
            }
        )
        surfaces = [
            surface.model_copy(
                update={"code_evidence_ids": keep(surface.code_evidence_ids)}
            )
            for surface in profile.threat_surfaces
        ]
        return ProfileResult(profile=normalized_profile, threat_surfaces=surfaces)

    def _require_profile_evidence(self, state: AssessmentState, profile: ProfileResult) -> None:
        self._require_issued(state, *profile.profile.profile_evidence_ids)
        for surface in profile.threat_surfaces:
            self._require_issued(state, *surface.code_evidence_ids)

    @staticmethod
    def _require_issued(state: AssessmentState, *evidence_ids: str) -> None:
        for evidence_id in evidence_ids:
            if evidence_id not in state.evidence_ids:
                raise ValueError(f"unknown evidence id: {evidence_id}")

    @staticmethod
    def _one_for_hypothesis(items: list[Any], hypothesis_id: str) -> Any | None:
        return next((item for item in items if item.hypothesis_id == hypothesis_id), None)

    @staticmethod
    def _hypothesis_key(hypothesis: VulnerabilityHypothesis) -> str:
        return derive_hypothesis_id(hypothesis)

    @staticmethod
    def _add_finding(
        state: AssessmentState,
        adjudication: Adjudication,
        *,
        rebuttal: DefenderRebuttal | None = None,
        red_response: RedResponse | None = None,
    ) -> None:
        hypothesis = state.hypotheses[adjudication.hypothesis_id].hypothesis
        if any(finding.hypothesis_id == hypothesis.hypothesis_id for finding in state.findings):
            return
        strongest_rebuttal = list(rebuttal.arguments) if rebuttal is not None else []
        rebuttal_failure_reason = ""
        if rebuttal is not None and red_response is not None:
            rebuttal_failure_reason = " ".join(red_response.reasoning)
        state.findings.append(Finding(
            finding_id=f"finding-{hypothesis.hypothesis_id}",
            hypothesis_id=hypothesis.hypothesis_id,
            severity="medium",
            confidence=confidence_level(adjudication.confidence),
            confidence_score=adjudication.confidence,
            root_cause=hypothesis.root_cause,
            attack_path=hypothesis.attack_path,
            impact=hypothesis.impact,
            preconditions=hypothesis.preconditions,
            code_evidence_ids=adjudication.accepted_code_evidence_ids,
            graph_evidence_ids=adjudication.accepted_graph_evidence_ids,
            judge_rationale=list(adjudication.rationale),
            strongest_rebuttal=strongest_rebuttal,
            rebuttal_failure_reason=rebuttal_failure_reason,
            remediation="Validate untrusted input before it crosses this trust boundary.",
        ))

    def _checkpoint(self, state: AssessmentState) -> None:
        self._ledger.checkpoint(state)

    def _event(self, event: str, **details: Any) -> None:
        self._ledger.append_event(event, **details)
