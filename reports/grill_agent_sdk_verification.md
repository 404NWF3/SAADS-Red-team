# Claude Agent SDK Verification: Adversarial Repository Grill Agent

**Overall Status**: PASS WITH WARNINGS

**Summary**: Offline SDK configuration and unit gates pass. Live fixture assessment can complete end-to-end (`phase=complete`) with signed repository evidence, profiled threat surfaces, two empty discovery sweeps, and a user-facing report that omits coverage/resource sections. Full seeded-vulnerability acceptance (confirmed findings for the three planted flaws + rejected defended file-write) was **not** achieved in the successful complete run: discovery returned no durable hypotheses after evidence filtering. Later attempts after evidence-fallback fixes hit intermittent SDK `error_max_turns` / missing structured-output failures during discovery.

## Critical Issues

- None for offline SDK configuration or packaging.

## Warnings

1. **Live acceptance facts incomplete.** Best complete live run:
   - Path: `artifacts/grill_runs/20260804T120036Z-e5636d91`
   - `phase=complete`, `agent_calls_used=3`, `cost_usd≈3.31`, `threat_surfaces=5`, `evidence_ids=59`, `consecutive_empty_sweeps=2`
   - `hypotheses=0`, `findings=0` (model citations were filtered as unissued before surface-evidence fallback landed)
   - Fixture recursive SHA-256 unchanged before/after
   - Report contains required sections and omits coverage / resource-limit sections

2. **Intermittent live discovery reliability.** Subsequent runs after discovery hardening still failed with `team turn returned no structured output` or `error_max_turns` on red-team discovery despite `TEAM_MAX_TURNS=40`, `TEAM_BUDGET_USD=5.00`, profiling without subagents, and limited retries for missing structured output only.

3. **Plan deviations for live practicality** (documented):
   - `TEAM_MAX_TURNS=40` (plan text: 12)
   - `TEAM_BUDGET_USD=5.00` / `JUDGE_BUDGET_USD=2.00` (plan text: 1.50 / 0.75)
   - Profiling and discovery run with `enable_subagents=False`
   - Profile / debate citations are filtered or rebound to MCP-issued evidence IDs

## Passed Checks

### SDK installation & configuration

- `pyproject.toml` depends on `claude-agent-sdk==0.2.122`, `requires-python = ">=3.12"`.
- Runtime: Python 3.12.x, package imports cleanly via `uv`.

### Programmatic subagents

- `RED_SUBAGENTS` / `CODE_SUBAGENTS` defined as `AgentDefinition` with role-scoped tools and `permissionMode="dontAsk"`.
- Judge has `agents={}` and no `Agent` in `allowed_tools`.
- Profiling/discovery may disable subagents deliberately for structured-output reliability.

### Strict MCP + tool surface

- Live CLI wires only in-process MCP servers: `repository` and `security_graph`.
- `strict_mcp_config=True` on every team turn.
- No Write / Edit / Bash / Shell / WebFetch tools for grill teams.
- MCP tool annotations: read-only, non-destructive, idempotent, closed-world.

### Permissions, settings isolation, structured outputs, resume, hooks, cost

- `permission_mode="dontAsk"` (never `bypassPermissions` / `acceptEdits`).
- `setting_sources=[]` — target `.claude` / `CLAUDE.md` / Skills / hooks are not loaded as instructions.
- `.env` loaded only from SAADS project root.
- Every turn sets `output_format` JSON schema and validates with Pydantic.
- `resume=session_id` captured; session IDs persisted on `AssessmentState`.
- `PreToolUse` / `PostToolUse` hooks append auditable tool events.
- MCP-issued `CodeEvidence` / `GraphEvidence` IDs sync into the ledger after each turn.

### Offline gates

```text
uv run pytest -q
# latest controller run: 140+ grill tests green within full suite (231+ passed historically;
# current grill package: 140 passed, 1 skipped)

uv run python -m compileall -q saads_grill_agent
exit 0
```

## Live Assessment

### Fixture integrity (complete run `20260804T120036Z-e5636d91`)

- Hash method: sorted per-file SHA-256 manifest of `tests/fixtures/vulnerable_llm_app`, then SHA-256 of that manifest.
- Before/After: `ca89aa2ad094f08f89a1038d2ca95ad8bdf2c8538f42813b5a2e244ecc632032`
- Unchanged: **yes**

### Acceptance facts

| Fact | Result |
| --- | --- |
| Fixture hash unchanged | PASS |
| Confirmed findings have signed evidence IDs + judge confidence | NOT PRODUCED (0 findings) |
| Three seeded vulns reach confirmed/rejected/duplicate | NOT PRODUCED (0 hypotheses) |
| Defended file-write rejected with allowlist/approval evidence | NOT PRODUCED |
| No hypothesis bypasses code rebuttal + judge | N/A (no hypotheses debated) |
| Two empty discovery sweeps recorded | PASS |
| Generated tests outside fixture, marked unexecuted | PASS (none generated; path outside fixture) |
| report.md / findings.json / debate / audit ID agreement | PASS for empty findings set |
| report.md has no coverage / unreviewed-scope / resource-limit / human-validation sections | PASS |

### Result

**LIVE PARTIAL** — pipeline completes and remains read-only against the fixture; seeded-vulnerability adjudication still needs a more reliable discovery turn (or a follow-up live run after the surface-evidence fallback / discovery prompt fixes).

## Recommendations

- Re-run live acceptance once after discovery settles:  
  `uv run python -m saads_grill_agent start tests/fixtures/vulnerable_llm_app --authorization-ref "fixture-live-acceptance" --goal "审查提示注入、工具调用和敏感信息泄露" --max-cost-usd 25`
- Consider further reducing discovery schema complexity or splitting discovery into one-hypothesis-per-turn calls.
- Keep per-turn budgets elevated for DeepSeek + MCP tool traffic; restore plan defaults only after live discovery is stable.
