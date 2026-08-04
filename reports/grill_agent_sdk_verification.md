# Claude Agent SDK Verification: Adversarial Repository Grill Agent

**Overall Status**: FAIL

**Summary**: Offline SDK configuration and unit gates pass after raising `TEAM_MAX_TURNS` to 40 and tightening the profiling prompt. A fresh live fixture assessment then completed the profiling turn far enough to return structured output, but aborted with `Assessment failed: unknown evidence id: ev-main-chat` (fabricated / unissued evidence ID). Fixture SHA-256 manifest unchanged. Acceptance facts still not met.

## Critical Issues

- **Live acceptance still failed after the turn-budget fix (not an API-key / GraphRAG-index / network blocker).**

  ### Attempt A (pre-fix, committed in `75621c1`)

  Exact error:

  ```text
  Assessment failed: team turn failed: error_max_turns
  ```

  Run: `artifacts/grill_runs/20260804T090649Z-a17872c1` — stuck at `phase=intake` under `TEAM_MAX_TURNS=12`.

  ### Attempt B (post-fix `f468a3c`)

  Command:

  ```text
  uv run python -m saads_grill_agent start tests/fixtures/vulnerable_llm_app --authorization-ref "fixture-live-acceptance" --goal "审查提示注入、工具调用和敏感信息泄露" --max-cost-usd 25
  ```

  Exact error:

  ```text
  Assessment failed: unknown evidence id: ev-main-chat
  ```

  Run: `artifacts/grill_runs/20260804T092218Z-25a7de60` — disk checkpoint still `phase=intake`, `profile=null`, `hypotheses={}`, `findings=[]`, `issued_evidence=[]`, empty `code_evidence.jsonl`. Profiling returned a `ProfileResult` that cited `ev-main-chat`, which was not a ledger-issued signed evidence ID from `read_repository_snippet` / GraphRAG tools. Exit code `1`.

- Seeded-vuln terminal states, defended file-write rejection, empty discovery sweeps, unexecuted generated tests, and report/artifact ID agreement **were not produced**.

## Warnings

- `claude-agent-sdk` remains pinned at `0.2.122` (project-wide).
- `ClaudeAgentOptions.tools` is always `["Agent"]` even for the judge; isolation relies on empty `agents` and judge `allowed_tools` omitting `Agent`.
- Live MCP audit lists (`code_audit` / `graph_audit` in `__main__.py`) and PostToolUse hooks are not yet bridged into `AssessmentLedger.record_issued_evidence` / `state.register_evidence` during a turn; even successful tool-signed IDs would need that bridge before `_require_profile_evidence` can accept them. Attempt B’s fabricated `ev-main-chat` ID would fail regardless.

## Passed Checks

### SDK installation & configuration

- `pyproject.toml` depends on `claude-agent-sdk==0.2.122` and `requires-python = ">=3.12"`.
- Runtime: Python `3.12.12`, `claude-agent-sdk` `0.2.122` imports cleanly via `uv`.

### Programmatic subagents

- `saads_grill_agent/teams.py` defines `RED_SUBAGENTS` (`graph-grounder`, `attack-path-analyst`, `test-strategist`) and `CODE_SUBAGENTS` (`architecture-mapper`, `reachability-falsifier`, `control-verifier`) as `AgentDefinition` with role-scoped tools and `permissionMode="dontAsk"`.
- Judge role returns `agents={}` and has no `Agent` in `allowed_tools`.

### Strict MCP + tool surface

- Live CLI wires only in-process MCP servers: `repository` and `security_graph`.
- `strict_mcp_config=True` on every team turn.
- Allowed MCP tools: repository list/search/snippet (+ GraphRAG for red/judge only).
- No Write, Edit, Bash, Shell, WebFetch, or other network/execute tools for grill teams.
- Repository and security-graph tools use read-only MCP annotations.

### Permissions, settings isolation, structured outputs, resume, hooks, cost / turns

- `permission_mode="dontAsk"`; `setting_sources=[]` (target instructions not loaded).
- `.env` loaded only from SAADS project root.
- Structured `output_format` + local Pydantic validation; session `resume`; Pre/Post tool hooks.
- Cost caps unchanged: team `max_budget_usd=1.50`, judge `0.75`.
- **Turn budget fix:** `TEAM_MAX_TURNS=40` for red/code team turns; `JUDGE_MAX_TURNS=12` unchanged; optional `run_turn(..., max_turns=)` override supported.
- Profiling prompt instructs minimal tool use (`list_repository` + few targeted snippets) and ASAP `ProfileResult`.

### Offline gates (post-fix)

```text
uv run pytest tests/saads_grill_agent -q
137 passed, 1 skipped in 7.53s

uv run pytest -q
231 passed, 1 skipped in 8.28s
```

## Recommendations

- Wire MCP-issued evidence from live tool audits into `ledger.record_issued_evidence` / `state.register_evidence` before profile/hypothesis validation.
- Strengthen prompts (and/or reject turns) so agents may only cite `code-*` / GraphRAG evidence IDs returned by tools.
- Keep judge `max_turns=12` unless judge turns also exhaust.

## Live Assessment

### Fixture integrity (Attempt B)

- Hash method: sorted per-file SHA-256 manifest excluding `.pytest_cache`, then SHA-256 of that manifest.
- Before: `411ae35b28f3b6f1fb7a90105bf04b4733789087862ccd28a83ff81d4a7a8e87`
- After: `411ae35b28f3b6f1fb7a90105bf04b4733789087862ccd28a83ff81d4a7a8e87`
- Unchanged: **yes**

### Acceptance facts (Attempt B)

| Fact | Result |
| --- | --- |
| Fixture hash unchanged | PASS |
| Confirmed findings have signed evidence IDs + judge confidence | NOT PRODUCED |
| Three seeded vulns reach confirmed/rejected/duplicate | NOT PRODUCED |
| Defended file-write rejected with allowlist/approval evidence | NOT PRODUCED |
| No hypothesis bypasses code rebuttal + judge | NOT PRODUCED |
| Two empty discovery sweeps recorded | NOT PRODUCED |
| Generated tests outside fixture, marked unexecuted | NOT PRODUCED |
| report.md / findings.json / debate / audit ID agreement | NOT PRODUCED |
| report.md has no coverage / unreviewed-scope / resource-limit / human-validation sections | N/A |

### Result

**LIVE FAILED** — `unknown evidence id: ev-main-chat` at `artifacts/grill_runs/20260804T092218Z-25a7de60`. Prior `error_max_turns` is addressed by `TEAM_MAX_TURNS=40`; live acceptance still incomplete.
