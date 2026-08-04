# Claude Agent SDK Verification: Adversarial Repository Grill Agent

**Overall Status**: FAIL

**Summary**: Offline SDK configuration and unit gates pass. An authorized live fixture assessment was attempted twice (`start`, then `resume`) against `tests/fixtures/vulnerable_llm_app`. Both attempts reached the live Claude Agent SDK / DeepSeek path and GraphRAG load, then aborted on the first code-team profiling turn with `Assessment failed: team turn failed: error_max_turns`. The fixture recursive SHA-256 manifest was unchanged. Acceptance facts could not be validated because the run never left `phase=intake` with empty hypotheses/findings.

## Critical Issues

- **Live acceptance failed (not an API-key / GraphRAG-index / network blocker).** Exact error:

  ```text
  Assessment failed: team turn failed: error_max_turns
  ```

  Observed on:
  1. `uv run python -m saads_grill_agent start tests/fixtures/vulnerable_llm_app --authorization-ref "fixture-live-acceptance" --goal "审查提示注入、工具调用和敏感信息泄露" --max-cost-usd 25`
  2. `uv run python -m saads_grill_agent resume artifacts/grill_runs/20260804T090649Z-a17872c1`

  Run directory: `artifacts/grill_runs/20260804T090649Z-a17872c1` (`authorization_ref=fixture-live-acceptance`, `snapshot_id=snap-cbb9c91fe566e516`). `run_state.json` remains `phase=intake`, `profile=null`, `hypotheses={}`, `findings=[]`, `team_sessions={}`. Exit code `1` (not resumable interrupted state `3`).

- Seeded-vuln terminal states, defended file-write rejection, empty discovery sweeps, unexecuted generated tests, and report/artifact ID agreement **were not produced** by a completed live run.

## Warnings

- `claude-agent-sdk` remains pinned at `0.2.122` (project-wide).
- `ClaudeAgentOptions.tools` is always `["Agent"]` even for the judge; isolation relies on empty `agents` and judge `allowed_tools` omitting `Agent`.
- Live failure mode is `error_max_turns` on the profiling turn (`max_turns=12`), suggesting the live model/session exhausted turns before structured `ProfileResult` output rather than a missing credential/index.

## Passed Checks

### SDK installation & configuration

- `pyproject.toml` depends on `claude-agent-sdk==0.2.122` and `requires-python = ">=3.12"`.
- Runtime: Python `3.12.12`, `claude-agent-sdk` `0.2.122` imports cleanly via `uv`.

### Programmatic subagents

- `saads_grill_agent/teams.py` defines `RED_SUBAGENTS` (`graph-grounder`, `attack-path-analyst`, `test-strategist`) and `CODE_SUBAGENTS` (`architecture-mapper`, `reachability-falsifier`, `control-verifier`) as `AgentDefinition` with role-scoped tools and `permissionMode="dontAsk"`.
- Judge role returns `agents={}` and has no `Agent` in `allowed_tools`.

### Strict MCP + tool surface

- Live CLI wires only in-process MCP servers: `repository` (`create_repository_server`) and `security_graph` (`create_security_graph_server`).
- `strict_mcp_config=True` on every team turn.
- Allowed MCP tools for grill teams:
  - `mcp__repository__list_repository`
  - `mcp__repository__search_repository`
  - `mcp__repository__read_repository_snippet`
  - `mcp__security_graph__query_security_graph` (red + judge only; code team / code subagents do not get GraphRAG)
- Repository and security-graph MCP tools use `ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)`.
- No Write, Edit, Bash, Shell, WebFetch, or other network/execute tools are registered for grill teams.

### Permissions, settings isolation, structured outputs, resume, hooks, cost

- `permission_mode="dontAsk"` (never `bypassPermissions` / `acceptEdits`).
- `setting_sources=[]` so target-repo `.claude` / `CLAUDE.md` / Skills / hooks are not loaded as instructions; repository content is untrusted data via read-only MCP only.
- `.env` is loaded only from the SAADS project root in `run_live_assessment` (`load_dotenv(PROJECT_ROOT / ".env")`), not from the target fixture.
- Every turn sets `output_format={"type": "json_schema", "schema": ...}` and validates with Pydantic locally.
- `resume=session_id` is passed; `ResultMessage.session_id` is captured for persistence.
- `PreToolUse` / `PostToolUse` hooks append auditable tool events.
- Cost limits: team turns `max_budget_usd=1.50`, judge turns `0.75`, `max_turns=12`; CLI `--max-cost-usd` defaults to 25.

### Target-instruction isolation

- `cwd` is the resolved target repository for session continuity, but with `setting_sources=[]` the SDK does not load target project settings/instructions.
- CLI rejects remote URLs; requires nonempty `--authorization-ref`.
- Resume fails closed on repository snapshot mismatch.

### Offline gates

```text
uv run pytest -q
231 passed, 1 skipped in 8.19s

uv run python -m compileall -q saads_grill_agent
exit 0
```

## Recommendations

- Investigate why the live profiling turn hits `error_max_turns` under DeepSeek (`deepseek-v4-flash`) with structured output + repository MCP + subagents; consider richer profiling prompts, higher `max_turns` for profile-only turns, or confirming structured-output+tool support for the configured model.
- Consider setting judge `tools=[]` (or omitting `Agent`) for clarity while keeping `allowed_tools` as the hard allowlist.
- Keep the SDK pin aligned with the rest of the monorepo unless a coordinated upgrade is planned.

## Live Assessment

### Command

```text
uv run python -m saads_grill_agent start tests/fixtures/vulnerable_llm_app --authorization-ref "fixture-live-acceptance" --goal "审查提示注入、工具调用和敏感信息泄露" --max-cost-usd 25
```

Resume retry:

```text
uv run python -m saads_grill_agent resume artifacts/grill_runs/20260804T090649Z-a17872c1
```

### Fixture integrity

- Hash method: sorted per-file SHA-256 manifest of all fixture files excluding `.pytest_cache`, then SHA-256 of that manifest.
- Before manifest digest: `411ae35b28f3b6f1fb7a90105bf04b4733789087862ccd28a83ff81d4a7a8e87`
- After start+resume digest: `411ae35b28f3b6f1fb7a90105bf04b4733789087862ccd28a83ff81d4a7a8e87`
- Unchanged: **yes**

### Live environment (not blocked)

- `DEEPSEEK_API_KEY` present; GraphRAG tables under `output/*.parquet` present; `settings.yaml` present; `GRAPHRAG_API_KEY` present.
- Failure is application/SDK turn exhaustion, not missing keys/index/network.

### Acceptance facts

| Fact | Result |
| --- | --- |
| Fixture hash unchanged | PASS |
| Confirmed findings have signed evidence IDs + judge confidence | NOT PRODUCED |
| Three seeded vulns reach confirmed/rejected/duplicate | NOT PRODUCED |
| Defended file-write rejected with allowlist/approval evidence | NOT PRODUCED |
| No hypothesis bypasses code rebuttal + judge | NOT PRODUCED |
| Two empty discovery sweeps recorded | NOT PRODUCED |
| Generated tests outside fixture, marked unexecuted | NOT PRODUCED |
| report.md / findings.json / debate / audit ID agreement | NOT PRODUCED (empty ledger stubs only) |
| report.md has no coverage / unreviewed-scope / resource-limit / human-validation sections | N/A (empty report stub from ledger create) |

### Result

**LIVE FAILED** — `error_max_turns` on profiling; incomplete run at `artifacts/grill_runs/20260804T090649Z-a17872c1`. Do not treat as a successful live acceptance.
