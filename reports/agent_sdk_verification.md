# Claude Agent SDK verification

**Overall Status**: PASS WITH WARNINGS

**Summary**: The Python 3.12 application uses `claude-agent-sdk` 0.2.122 with the current documented `query()` pattern, loads project settings and the `collect-defense-corpus` project Skill, and exposes only the tools needed by the workflow.

**Critical Issues**: None.

**Warnings**:

- A live Claude service call was not executed because this checkout does not currently expose an `ANTHROPIC_API_KEY` variable. Import, option construction, CLI startup, Skill validation, and permission behavior were verified locally.

**Passed Checks**:

- `pyproject.toml` and `uv.lock` reproducibly pin GraphRAG 3.1.1 and Claude Agent SDK 0.2.122.
- `.env.example` documents `ANTHROPIC_API_KEY`; `.env` is ignored and no credential is hardcoded.
- `query()` receives `ClaudeAgentOptions` with `cwd`, `setting_sources=["project"]`, and `skills=["collect-defense-corpus"]`.
- Read-only tools are preapproved; Bash is gated to the collector, offline validator, and GraphRAG dry-run commands.
- SDK and result errors return a nonzero process status.
- `uv run python main.py --help`, Python bytecode compilation, and all tests pass.

**Recommendations**:

- Set `ANTHROPIC_API_KEY` or use a valid Claude Code login before running `uv run python main.py`.
- Keep acquisition logic in the deterministic collector and use the Agent only for orchestration and audit.
