from __future__ import annotations

import json
import re
from pathlib import Path

from saads_grill_agent.contracts import (
    AssessmentConfig,
    AssessmentState,
    Finding,
    HypothesisRecord,
    RepositoryProfile,
    ThreatSurface,
    VulnerabilityHypothesis,
)
from saads_grill_agent.report import (
    confidence_level,
    derive_severity,
    render_report,
    write_reports,
)


def _profile() -> RepositoryProfile:
    return RepositoryProfile(
        snapshot_id="snap-1",
        model_provider="deepseek",
        model_name="deepseek-v4",
        agent_framework="claude-agent-sdk",
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
        profile_evidence_ids=["code-profile-1"],
        supplied_profile_conflicts=[],
    )


def _hypothesis(
    hypothesis_id: str,
    *,
    title: str,
    root_cause: str = "Untrusted retrieval content reaches the system prompt.",
    impact: str = "Instruction hijack revealing protected secrets.",
    preconditions: list[str] | None = None,
) -> VulnerabilityHypothesis:
    return VulnerabilityHypothesis(
        hypothesis_id=hypothesis_id,
        surface_id="surf-rag",
        title=title,
        root_cause=root_cause,
        attack_path=[
            "attacker controls a retrieved document",
            "model obeys the injected instruction at app/rag.py:41",
        ],
        impact=impact,
        preconditions=preconditions
        or ["default reachable unauthenticated retrieval path"],
        code_evidence_ids=["code-rag-41"],
        graph_evidence_ids=[],
    )


def state_with_all_terminal_states() -> AssessmentState:
    state = AssessmentState(
        config=AssessmentConfig(
            target_repo=Path("review-target"),
            goal="审查该 LLM 应用的代码级安全漏洞",
        ),
        snapshot_id="snap-1",
        phase="complete",
        profile=_profile(),
        threat_surfaces=[
            ThreatSurface(
                surface_id="surf-rag",
                kind="rag_retrieval",
                name="RAG retrieval boundary",
                entrypoints=["app/rag.py:41"],
                trust_transition="untrusted document -> trusted prompt",
                assets=["system prompt", "user session data"],
                code_evidence_ids=["code-rag-41"],
            )
        ],
        agent_calls_used=12,
        cost_usd_used=3.5,
    )
    state.register_evidence("code-rag-41", "code-profile-1", "code-tool-1")

    confirmed = _hypothesis("hyp-confirmed", title="RAG prompt injection")
    rejected = _hypothesis(
        "hyp-rejected",
        title="File-write tool abuse",
        root_cause="Tool allows arbitrary path writes.",
        impact="Privileged tool effect writing secrets to disk.",
        preconditions=["caller holds admin role", "non-default tool enabled"],
    )
    duplicate = _hypothesis(
        "hyp-duplicate",
        title="Same RAG injection restated",
    )

    state.hypotheses = {
        "hyp-confirmed": HypothesisRecord(
            hypothesis=confirmed,
            status="confirmed",
            final_adjudication_id="adj-1",
        ),
        "hyp-rejected": HypothesisRecord(
            hypothesis=rejected,
            status="rejected",
            final_adjudication_id="adj-2",
        ),
        "hyp-duplicate": HypothesisRecord(
            hypothesis=duplicate,
            status="duplicate",
            final_adjudication_id="adj-3",
        ),
    }
    state.findings = [
        Finding(
            finding_id="finding-hyp-confirmed",
            hypothesis_id="hyp-confirmed",
            severity="low",
            confidence="low",
            root_cause=confirmed.root_cause,
            attack_path=confirmed.attack_path,
            impact=confirmed.impact,
            preconditions=confirmed.preconditions,
            code_evidence_ids=["code-rag-41"],
            graph_evidence_ids=[],
            remediation="Separate trusted instructions from retrieved context.",
            generated_test_ids=["test-1"],
        )
    ]
    return state


def test_report_separates_confirmed_rejected_and_duplicate_items() -> None:
    report = render_report(state_with_all_terminal_states())

    assert "## 已确认漏洞" in report
    assert "## 已驳回假设" in report
    assert "app/rag.py:41" in report
    assert "## 证据与裁决审计" in report
    assert "攻击面覆盖与盲区" not in report
    assert "资源限制" not in report


def test_report_includes_required_sections_only() -> None:
    report = render_report(state_with_all_terminal_states())

    for heading in (
        "## 运行元数据与目标快照",
        "## 执行摘要",
        "## 仓库架构与信任边界",
        "## 严重级别统计",
        "## 已确认漏洞",
        "## 已驳回假设",
        "## 生成测试清单",
        "## 证据与裁决审计",
    ):
        assert heading in report

    for forbidden in (
        "攻击面覆盖与盲区",
        "资源限制",
        "coverage matrix",
        "unreviewed",
        "human-validation",
        "人工确认",
    ):
        assert forbidden not in report.lower() if forbidden.isascii() else forbidden not in report


def _section_body(report: str, heading: str) -> str:
    rest = report.split(heading, 1)[1]
    next_heading = re.search(r"\n## ", rest)
    return rest if next_heading is None else rest[: next_heading.start()]


def test_report_lists_rejected_and_duplicate_under_rejected_section() -> None:
    report = render_report(state_with_all_terminal_states())
    rejected_section = _section_body(report, "## 已驳回假设")

    assert "hyp-rejected" in rejected_section
    assert "hyp-duplicate" in rejected_section
    assert "hyp-confirmed" not in rejected_section


def test_report_escapes_untrusted_markdown_and_html() -> None:
    state = state_with_all_terminal_states()
    finding = state.findings[0]
    state.findings[0] = finding.model_copy(
        update={
            "root_cause": "<script>alert(1)</script> and ## injected",
            "remediation": "use `rm -rf /` carefully",
        }
    )
    state.hypotheses["hyp-confirmed"] = HypothesisRecord(
        hypothesis=_hypothesis(
            "hyp-confirmed",
            title="Evil </details> title with **boom**",
        ),
        status="confirmed",
        final_adjudication_id="adj-1",
    )

    report = render_report(state)

    assert "<script>" not in report
    assert "&lt;script&gt;" in report
    assert "\\#\\# injected" in report
    assert report.count("## 已确认漏洞") == 1


def test_confidence_level_thresholds() -> None:
    assert confidence_level(0.80) == "high"
    assert confidence_level(1.0) == "high"
    assert confidence_level(0.55) == "medium"
    assert confidence_level(0.79) == "medium"
    assert confidence_level(0.549) == "low"
    assert confidence_level(0.0) == "low"


def test_derive_severity_uses_impact_exploitability_matrix() -> None:
    assert (
        derive_severity(
            impact="Exfiltrates secrets and API keys from memory.",
            preconditions=["default public unauthenticated chat endpoint"],
        )
        == "critical"
    )
    assert (
        derive_severity(
            impact="Cross-user data disclosure via shared session memory.",
            preconditions=["attacker is an authenticated tenant user"],
        )
        == "high"
    )
    assert (
        derive_severity(
            impact="Unauthorized model behavior changes the answer tone.",
            preconditions=["requires privileged admin console access"],
        )
        == "low"
    )
    assert (
        derive_severity(
            impact="Bounded quality degradation in summaries.",
            preconditions=["user-assisted paste of a document"],
        )
        == "low"
    )


def test_write_reports_writes_markdown_and_findings_json(tmp_path: Path) -> None:
    state = state_with_all_terminal_states()
    write_reports(state, tmp_path)

    report_path = tmp_path / "report.md"
    findings_path = tmp_path / "findings.json"
    assert report_path.is_file()
    assert findings_path.is_file()

    report = report_path.read_text(encoding="utf-8")
    assert "## 已确认漏洞" in report
    assert "app/rag.py:41" in report

    payload = json.loads(findings_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 1
    finding = payload[0]
    assert finding["finding_id"] == "finding-hyp-confirmed"
    assert finding["severity"] == "critical"
    assert finding["confidence"] in {"high", "medium", "low"}
    assert "app/rag.py:41" in " ".join(finding["attack_path"])


def test_render_report_is_deterministic() -> None:
    state = state_with_all_terminal_states()
    assert render_report(state) == render_report(state)


def test_confirmed_finding_section_includes_required_fields() -> None:
    report = render_report(state_with_all_terminal_states())
    confirmed = _section_body(report, "## 已确认漏洞")

    for needle in (
        "根因",
        "攻击路径",
        "攻击者前置条件",
        "影响",
        "代码证据",
        "置信度",
        "修复建议",
        "测试产物状态",
        "code-rag-41",
        "unexecuted",
    ):
        assert needle in confirmed
