"""Deterministic Markdown/JSON report rendering for grill assessments."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from saads_grill_agent.contracts import (
    AssessmentState,
    ConfidenceLevel,
    Finding,
    HypothesisRecord,
    Severity,
)
from saads_grill_agent.test_artifacts import TestArtifactStatus


_IMPACT_HIGH = re.compile(
    r"secret|credential|api[\s_-]?key|password|token|privileged\s+tool|"
    r"cross[\s_-]?user|code\s+execution|\brce\b|arbitrary\s+code|"
    r"远程代码|密钥|凭据|越权读写|跨用户",
    re.IGNORECASE,
)
_IMPACT_MEDIUM = re.compile(
    r"integrity|unauthorized\s+model|non[\s_-]?secret\s+disclosure|"
    r"instruction\s+hijack|prompt\s+injection|disclosure|exfiltrat|"
    r"完整性|未授权|提示注入|指令劫持|泄露",
    re.IGNORECASE,
)
_IMPACT_LOW = re.compile(
    r"quality\s+degradation|bounded|latency|availability\s+nuisance|"
    r"质量下降|有界|性能退化",
    re.IGNORECASE,
)
_EXPLOIT_HIGH = re.compile(
    r"unauthenticated|anonymous|public\s+endpoint|default\s+reachable|"
    r"default\s+public|no\s+auth|未认证|匿名|默认可达|公开接口",
    re.IGNORECASE,
)
_EXPLOIT_MEDIUM = re.compile(
    r"authenticated|user[\s_-]?assisted|logged[\s_-]?in|tenant\s+user|"
    r"已认证|用户辅助|登录用户",
    re.IGNORECASE,
)
_EXPLOIT_LOW = re.compile(
    r"privileged|admin|non[\s_-]?default|operator\s+access|"
    r"特权|管理员|非默认",
    re.IGNORECASE,
)

_SEVERITY_MATRIX: dict[str, dict[str, Severity]] = {
    "high": {"high": "critical", "medium": "high", "low": "medium"},
    "medium": {"high": "high", "medium": "medium", "low": "low"},
    "low": {"high": "medium", "medium": "low", "low": "low"},
}

def confidence_level(score: float) -> ConfidenceLevel:
    """Map a judge confidence score to a discrete confidence label."""
    if score >= 0.80:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def classify_impact(impact: str) -> str:
    """Classify impact magnitude from finding/hypothesis impact text."""
    if _IMPACT_HIGH.search(impact):
        return "high"
    if _IMPACT_LOW.search(impact) and not _IMPACT_MEDIUM.search(impact):
        return "low"
    if _IMPACT_MEDIUM.search(impact):
        return "medium"
    return "medium"


def classify_exploitability(preconditions: Iterable[str]) -> str:
    """Classify exploitability from attacker precondition text."""
    joined = " ".join(preconditions)
    if _EXPLOIT_HIGH.search(joined):
        return "high"
    if _EXPLOIT_LOW.search(joined) and not _EXPLOIT_MEDIUM.search(joined):
        return "low"
    if _EXPLOIT_MEDIUM.search(joined):
        return "medium"
    return "medium"


def derive_severity(*, impact: str, preconditions: Iterable[str]) -> Severity:
    """Derive severity locally from impact × exploitability."""
    impact_level = classify_impact(impact)
    exploit_level = classify_exploitability(preconditions)
    return _SEVERITY_MATRIX[impact_level][exploit_level]


def escape_text(value: str) -> str:
    """Escape untrusted model text so it cannot inject Markdown structure."""
    escaped = (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("#", "\\#")
    )
    return escaped


def finalize_finding(finding: Finding) -> Finding:
    """Return a finding with locally derived severity and confidence."""
    return finding.model_copy(
        update={
            "severity": derive_severity(
                impact=finding.impact,
                preconditions=finding.preconditions,
            ),
            "confidence": confidence_level(finding.confidence_score),
        }
    )


_GRAPH_SKIP_LABELS: dict[str, str] = {
    "disabled_by_config": "配置关闭（`use_graphrag: false` 或 `--no-graphrag`）",
    "index_unavailable": "项目 GraphRAG 索引不可用（缺少 settings.yaml 或必需 parquet）",
    "index_load_failed": "GraphRAG 索引加载失败，已降级为仅仓库证据",
}


def render_report(state: AssessmentState) -> str:
    """Render a deterministic user-facing Markdown report from assessment state."""
    finalized = [finalize_finding(finding) for finding in state.findings]
    sections = [
        _section_metadata(state),
        _section_knowledge_grounding(state),
        _section_executive_summary(state, finalized),
        _section_architecture(state),
        _section_severity_counts(finalized),
        _section_confirmed(state, finalized),
        _section_rejected(state),
        _section_test_manifest(finalized),
        _section_audit(state, finalized),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def write_reports(state: AssessmentState, run_dir: Path) -> None:
    """Write report.md and findings.json under the assessment run directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    finalized = [finalize_finding(finding) for finding in state.findings]
    report = render_report(state)
    (run_dir / "report.md").write_text(report, encoding="utf-8", newline="\n")
    payload = [finding.model_dump(mode="json") for finding in finalized]
    (run_dir / "findings.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _section_metadata(state: AssessmentState) -> str:
    target = state.config.target_repo
    target_display = (
        "<redacted-path>"
        if target.is_absolute()
        else escape_text(str(target))
    )
    lines = [
        "## 运行元数据与目标快照",
        f"- 快照 ID: `{escape_text(state.snapshot_id)}`",
        f"- 阶段: `{escape_text(state.phase)}`",
        f"- 目标仓库: `{target_display}`",
        f"- 审查目标: {escape_text(state.config.goal)}",
        f"- Agent 调用次数: {state.agent_calls_used}",
        f"- 累计费用 (USD): {state.cost_usd_used}",
    ]
    if state.profile is not None:
        profile = state.profile
        lines.extend(
            [
                f"- 模型提供方: {escape_text(profile.model_provider)}",
                f"- 模型名称: {escape_text(profile.model_name)}",
                f"- Agent 框架: {escape_text(profile.agent_framework)}",
            ]
        )
    return "\n".join(lines)


def _section_knowledge_grounding(state: AssessmentState) -> str:
    lines = ["## 知识接地"]
    if state.graph_enabled:
        lines.append(
            "- GraphRAG：已启用（红队 / 裁判可软引用项目安全知识图谱与 "
            "`ground-red-team-evidence` Skill）"
        )
    elif state.graph_skipped_reason:
        reason = _GRAPH_SKIP_LABELS.get(
            state.graph_skipped_reason,
            state.graph_skipped_reason,
        )
        lines.append(f"- GraphRAG：未启用 — {escape_text(reason)}")
    else:
        lines.append("- GraphRAG：未启用")
    lines.append(
        f"- 操作员配置 `use_graphrag`："
        f"{'是' if state.config.use_graphrag else '否'}"
    )
    return "\n".join(lines)


def _section_executive_summary(
    state: AssessmentState, findings: list[Finding]
) -> str:
    rejected = _records_with_status(state, "rejected")
    duplicates = _records_with_status(state, "duplicate")
    return "\n".join(
        [
            "## 执行摘要",
            (
                f"本次评估共确认 {len(findings)} 个漏洞，驳回 {len(rejected)} 个假设，"
                f"标记重复 {len(duplicates)} 个假设；当前阶段为 `{escape_text(state.phase)}`。"
            ),
        ]
    )


def _section_architecture(state: AssessmentState) -> str:
    lines = ["## 仓库架构与信任边界"]
    profile = state.profile
    if profile is None:
        lines.append("尚未完成仓库画像。")
        return "\n".join(lines)

    lines.append(
        "- 前端根目录: "
        + (", ".join(escape_text(item) for item in profile.frontend_roots) or "（无）")
    )
    lines.append(
        "- 后端根目录: "
        + (", ".join(escape_text(item) for item in profile.backend_roots) or "（无）")
    )
    for label, sites in (
        ("模型调用点", profile.model_call_sites),
        ("提示拼装点", profile.prompt_assembly_sites),
        ("工具定义点", profile.tool_definition_sites),
        ("检索与摄入点", profile.retrieval_and_ingestion_sites),
        ("身份与授权点", profile.authn_authz_sites),
    ):
        if sites:
            lines.append(
                f"- {label}: " + ", ".join(escape_text(site) for site in sites)
            )

    if state.threat_surfaces:
        lines.append("- 信任边界:")
        for surface in state.threat_surfaces:
            entrypoints = ", ".join(
                escape_text(item) for item in surface.entrypoints
            )
            lines.append(
                f"  - `{escape_text(surface.surface_id)}` "
                f"{escape_text(surface.name)}: {escape_text(surface.trust_transition)} "
                f"(入口 {entrypoints})"
            )
    return "\n".join(lines)


def _section_severity_counts(findings: list[Finding]) -> str:
    counts = Counter(finding.severity for finding in findings)
    order: tuple[Severity, ...] = ("critical", "high", "medium", "low")
    lines = ["## 严重级别统计"]
    for level in order:
        lines.append(f"- {level}: {counts.get(level, 0)}")
    return "\n".join(lines)


def _section_confirmed(state: AssessmentState, findings: list[Finding]) -> str:
    lines = ["## 已确认漏洞"]
    if not findings:
        lines.append("无已确认漏洞。")
        return "\n".join(lines)

    for finding in findings:
        record = state.hypotheses.get(finding.hypothesis_id)
        title = (
            record.hypothesis.title
            if record is not None
            else finding.finding_id
        )
        test_status = _test_artifact_status(finding)
        lines.extend(
            [
                f"**{escape_text(finding.finding_id)} — {escape_text(title)}**",
                f"- 严重级别: `{finding.severity}`",
                f"- 置信度: `{finding.confidence}` (score={finding.confidence_score})",
                f"- 根因: {escape_text(finding.root_cause)}",
                "- 攻击路径:",
                *[f"  - {escape_text(step)}" for step in finding.attack_path],
                "- 攻击者前置条件:",
                *(
                    [f"  - {escape_text(item)}" for item in finding.preconditions]
                    or ["  - （无）"]
                ),
                f"- 影响: {escape_text(finding.impact)}",
                "- 代码证据: "
                + (
                    ", ".join(
                        f"`{escape_text(item)}`"
                        for item in finding.code_evidence_ids
                    )
                    or "（无）"
                ),
                "- GraphRAG 证据: "
                + (
                    ", ".join(
                        f"`{escape_text(item)}`"
                        for item in finding.graph_evidence_ids
                    )
                    or "（无）"
                ),
                "- 防御方最强反驳:",
                *(
                    [f"  - {escape_text(item)}" for item in finding.strongest_rebuttal]
                    or ["  - （未记录）"]
                ),
                "- 反驳为何失败: "
                + (
                    escape_text(finding.rebuttal_failure_reason)
                    if finding.rebuttal_failure_reason
                    else "（未记录）"
                ),
                "- 裁判理由:",
                *[f"  - {escape_text(item)}" for item in finding.judge_rationale],
                f"- 修复建议: {escape_text(finding.remediation)}",
                f"- 测试产物状态: `{test_status}`",
            ]
        )
    return "\n".join(lines)


def _section_rejected(state: AssessmentState) -> str:
    lines = ["## 已驳回假设"]
    records = _records_with_status(state, "rejected") + _records_with_status(
        state, "duplicate"
    )
    if not records:
        lines.append("无已驳回或重复假设。")
        return "\n".join(lines)

    for record in records:
        hypothesis = record.hypothesis
        status_label = "重复" if record.status == "duplicate" else "驳回"
        lines.extend(
            [
                f"- `{escape_text(hypothesis.hypothesis_id)}` [{status_label}] "
                f"{escape_text(hypothesis.title)}",
                f"- 根因: {escape_text(hypothesis.root_cause)}",
                f"- 影响: {escape_text(hypothesis.impact)}",
                f"- 裁决 ID: `{escape_text(record.final_adjudication_id or '')}`",
            ]
        )
    return "\n".join(lines)


def _section_test_manifest(findings: list[Finding]) -> str:
    lines = ["## 生成测试清单"]
    rows = [
        (finding.finding_id, test_id, _test_artifact_status(finding))
        for finding in findings
        for test_id in finding.generated_test_ids
    ]
    if not rows:
        lines.append("无已生成测试产物。")
        return "\n".join(lines)
    for finding_id, test_id, status in rows:
        lines.append(
            f"- `{escape_text(test_id)}` → finding `{escape_text(finding_id)}` "
            f"[{status}]"
        )
    return "\n".join(lines)


def _section_audit(state: AssessmentState, findings: list[Finding]) -> str:
    lines = ["## 证据与裁决审计"]
    lines.append(
        "- 已登记证据 ID: "
        + (
            ", ".join(f"`{escape_text(item)}`" for item in state.evidence_ids)
            or "（无）"
        )
    )
    for record in state.hypotheses.values():
        lines.append(
            f"- 假设 `{escape_text(record.hypothesis.hypothesis_id)}`: "
            f"状态 `{record.status}`，裁决 "
            f"`{escape_text(record.final_adjudication_id or '无')}`"
        )
    for finding in findings:
        lines.append(
            f"- 漏洞 `{escape_text(finding.finding_id)}`: "
            f"severity=`{finding.severity}` confidence=`{finding.confidence}` "
            f"证据="
            + ", ".join(
                f"`{escape_text(item)}`"
                for item in (
                    finding.code_evidence_ids + finding.graph_evidence_ids
                )
            )
        )
    for surface in state.threat_surfaces:
        for entrypoint in surface.entrypoints:
            lines.append(
                f"- 信任边界入口引用: `{escape_text(entrypoint)}` "
                f"(surface `{escape_text(surface.surface_id)}`)"
            )
    return "\n".join(lines)


def _records_with_status(
    state: AssessmentState, status: str
) -> list[HypothesisRecord]:
    return [
        record
        for record in state.hypotheses.values()
        if record.status == status
    ]


def _test_artifact_status(finding: Finding) -> str:
    if finding.generated_test_ids:
        return TestArtifactStatus.UNEXECUTED.value
    return TestArtifactStatus.GENERATION_FAILED.value
