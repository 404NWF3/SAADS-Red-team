import json
from pathlib import Path

run = Path(r"artifacts/grill_runs/20260804T120036Z-e5636d91")
state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
findings_raw = json.loads((run / "findings.json").read_text(encoding="utf-8"))
findings = findings_raw if isinstance(findings_raw, list) else findings_raw.get("findings", [])
report = (run / "report.md").read_text(encoding="utf-8")

print("phase", state.get("phase"))
print("calls", state.get("agent_calls_used"), "cost", state.get("cost_usd_used"))
print("surfaces", len(state.get("threat_surfaces") or []))
print("evidence", len(state.get("evidence_ids") or []))
print("empty_sweeps", (state.get("discovery") or {}).get("consecutive_empty_sweeps"))
hyps = state.get("hypotheses") or {}
print("hypotheses", len(hyps))
for hid, rec in hyps.items():
    h = rec.get("hypothesis") or {}
    print(f"  {hid}: status={rec.get('status')} title={h.get('title', '')[:100]}")
print("findings", len(findings))
for f in findings:
    code = f.get("code_evidence_ids") or []
    graph = f.get("graph_evidence_ids") or []
    print(
        f"  {f.get('finding_id')}: sev={f.get('severity')} conf={f.get('confidence')} "
        f"score={f.get('confidence_score')} evidence={code + graph} tests={f.get('generated_test_ids')}"
    )

checks = {
    "phase_complete": state.get("phase") == "complete",
    "has_evidence": len(state.get("evidence_ids") or []) > 0,
    "empty_sweeps_2": (state.get("discovery") or {}).get("consecutive_empty_sweeps") == 2,
    "report_confirmed": "## 已确认漏洞" in report,
    "report_rejected": "## 已驳回假设" in report,
    "report_audit": "## 证据与裁决审计" in report,
    "no_coverage": "攻击面覆盖与盲区" not in report,
    "no_resource": "资源限制" not in report,
}
if findings:
    checks["findings_have_evidence"] = all(
        (f.get("code_evidence_ids") or f.get("graph_evidence_ids"))
        and f.get("confidence_score") is not None
        for f in findings
    )
else:
    checks["findings_have_evidence"] = False

tests_dir = run / "tests"
test_files = [p for p in tests_dir.glob("*") if p.is_file()] if tests_dir.exists() else []
checks["tests_outside_fixture"] = all(
    "vulnerable_llm_app" not in str(p.resolve()) for p in test_files
)
print("test_files", [p.name for p in test_files])
print("CHECKS", json.dumps(checks, ensure_ascii=False, indent=2))
print(
    "confirmed",
    sum(1 for r in hyps.values() if r.get("status") == "confirmed"),
    "rejected",
    sum(1 for r in hyps.values() if r.get("status") == "rejected"),
    "duplicate",
    sum(1 for r in hyps.values() if r.get("status") == "duplicate"),
)
text = (json.dumps(hyps, ensure_ascii=False) + report).lower()
for kw in [
    "allowlist",
    "approval",
    "file-write",
    "file_write",
    "write_file",
    "rag",
    "prompt",
    "debug",
    "system prompt",
    "tool",
]:
    if kw in text:
        print("keyword_hit", kw)
