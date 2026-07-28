# Claude Agent SDK Verification: GraphRAG Attack Agent

**Overall Status**: PASS WITH WARNINGS

**Summary**: The Python 3.12 application uses Claude Agent SDK with the
DeepSeek Anthropic-compatible endpoint, loads three project Skills, exposes one
read-only in-process GraphRAG tool, validates both model stages with Pydantic,
and publishes only an offline JSON case and deterministic mock script. A live
DeepSeek + GraphRAG acceptance run completed successfully.

## Critical Issues

None.

## Warnings

- The repository remains pinned to `claude-agent-sdk==0.2.122`; PyPI listed
  `0.2.128` as current on 2026-07-28. The existing project Agent also uses the
  pinned version, and the implemented workflow passed live verification, so
  this feature does not force an unrelated dependency upgrade.
- A combined sdist-and-wheel build exceeded 120 seconds because the dirty
  repository contains large existing data artifacts. A wheel-only build
  completed successfully and contained all seven `saads_attack_agent` modules.
- The detailed architecture, contracts, layout, and commands are documented
  under `docs/superpowers/`; the existing README was not rewritten because it
  contains unrelated user changes.

## Passed Checks

- Python `3.12.12`, `claude-agent-sdk 0.2.122`, and `graphrag 3.1.1` import
  successfully through the locked `uv` environment.
- `ClaudeAgentOptions` uses `setting_sources=["project"]`, a per-phase `skills`
  list, `tools=["Skill"]`, `permission_mode="dontAsk"`, strict MCP
  configuration, and an allowlist containing only `Skill` and
  `mcp__security_graph__query_security_graph`.
- `DEEPSEEK_API_KEY` is mapped in process to `ANTHROPIC_API_KEY`;
  `ANTHROPIC_BASE_URL` is fixed to
  `https://api.deepseek.com/anthropic`; the configured DeepSeek model is passed
  both as the SDK model and `ANTHROPIC_MODEL`.
- No API key is hardcoded. `.env` is ignored, and `.env.example` documents only
  placeholder DeepSeek credentials for this Agent.
- The custom MCP tool has read-only, non-destructive, idempotent annotations.
  It accepts only the three declared query purposes and appends tool-returned
  evidence to an application-owned audit.
- Stage one enables only `recognize-attack-intent`. Stage two enables only
  `ground-attack-case` and `generate-offline-attack-script`.
- The SDK structured-output schema removes only Pydantic's unsupported
  `discriminator` annotation. The original Pydantic model still performs full
  local validation after SDK output.
- All three Skills pass `skill-creator/scripts/quick_validate.py` and the
  project discovery tests.
- Generated source is produced by deterministic family renderers, imports only
  `json`, and has no model-authored Python, network client, subprocess, URL, or
  external file access.
- Publication compiles and executes the script in an isolated temporary
  directory before atomically renaming the artifact directory.

## Verification Evidence

```text
uv run pytest -q
80 passed in 7.22s

uv run python -m compileall -q saads_attack_agent
exit 0

uv build --wheel
Successfully built llm_defense_graphrag-0.1.0-py3-none-any.whl
```

Live command:

```text
uv run python -m saads_attack_agent \
  Generate_an_indirect_prompt_injection_case_for_RAG_retrieval_context
```

Live result:

```text
case_id: case-4d90563c1b14
family: prompt_injection
GraphRAG purposes:
  - intent_classification
  - case_grounding
  - script_grounding
files:
  - attack_case.json
  - attack.py
attack.py: exit 0, offline_only=true, changed=true
```

## Recommendations

- Upgrade Claude Agent SDK in a separate dependency-maintenance change after
  rerunning both the existing corpus Agent verification and this live
  acceptance case.
- Add an explicit sdist exclusion policy for generated data if publishing an
  sdist becomes a project requirement.
