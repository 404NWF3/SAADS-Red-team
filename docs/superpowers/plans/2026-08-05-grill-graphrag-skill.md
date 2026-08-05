# Grill GraphRAG Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `saads_grill_agent` optionally load GraphRAG via probe-then-load, soft-guide red_team/judge with Skill `ground-red-team-evidence`, and never fail a run merely because the index is missing or `--no-graphrag` is set.

**Architecture:** `graph_enabled = use_graphrag AND probe(PROJECT_ROOT)`. When enabled, hang `security_graph` MCP, load project Skill, keep `GRAPH_TOOL` for red/judge; when disabled, strip those and continue repo-only. SDK `cwd` is always SAADS `PROJECT_ROOT`. Orchestrator state machine stays unchanged; only turn prompts and `TeamBackend` options change.

**Tech Stack:** Python 3.12, Pydantic 2, pytest, Claude Agent SDK, existing `SecurityGraph` in `saads_attack_agent/security_graph.py`, YAML via `saads_grill_agent/runtime_config.py`.

**Spec:** `docs/superpowers/specs/2026-08-05-grill-graphrag-skill-design.md`

## Global Constraints

- Do not modify `saads_attack_agent` case-generation behavior; may import `SecurityGraph` / `REQUIRED_TABLES` only.
- Soft guidance only — no hard GraphRAG evidence quotas.
- Never load target-repo Skills (`setting_sources` must not discover target `.claude` while `cwd` is the target).
- `CLI > YAML > defaults` for `use_graphrag`; `--no-graphrag` forces false.
- Default tests must not call paid models or live GraphRAG completion.
- Subagents for this plan may only use models `cursor-grok-4.5-high-fast` or `composer-2.5-fast`.
- Do not rewrite discovery/debate state machine; prompt string tweaks only.
- Current workspace may already contain uncommitted YAML/`runtime_config` WIP — treat that as the foundation; do not revert unrelated WIP hunks.

## File Structure

| File | Role |
|---|---|
| `saads_grill_agent/graph_runtime.py` | `probe_graph_index`, `GraphRuntime` resolution (enabled + reason) |
| `saads_grill_agent/runtime_config.py` | `use_graphrag` on `RedTeamConfig` + CLI merge |
| `saads_grill_agent/contracts.py` | `AssessmentConfig.use_graphrag` |
| `saads_grill_agent/__main__.py` | `--no-graphrag`, optional load, resolved YAML fields |
| `saads_grill_agent/teams.py` | `project_root`, `graph_enabled`, cwd/skills/tools/agents |
| `saads_grill_agent/orchestrator.py` | Prompt appendices (grilling + Skill mention) |
| `saads_grill_agent/report.py` | Knowledge-grounding blurb |
| `.claude/skills/ground-red-team-evidence/SKILL.md` | New Skill |
| `red-team-config.yaml` | Document `use_graphrag` |
| `README.md` | One short grill note |
| `tests/saads_grill_agent/test_graph_runtime.py` | Probe + resolve tests |
| `tests/saads_grill_agent/test_runtime_config.py` | Config merge tests |
| `tests/saads_grill_agent/test_teams.py` | Tool/skill gating tests |
| `tests/saads_grill_agent/test_cli.py` | CLI / no-index path |

---

### Task 0: Land YAML config foundation on the feature branch (if missing)

**Files:**
- Ensure present: `saads_grill_agent/runtime_config.py`, `red-team-config.yaml`, related `__main__.py` / `contracts.py` (`SdkLimits`) / tests already in WIP

**Interfaces:**
- Produces: working `RedTeamConfig`, `load_red_team_config`, `merge_cli_over_config`, `AssessmentConfig.sdk`, CLI `--config`

- [ ] **Step 1: Verify foundation exists in the worktree**

Run: `uv run pytest tests/saads_grill_agent/test_runtime_config.py tests/saads_grill_agent/test_cli.py -q`

If `runtime_config.py` is missing, copy the WIP from the main checkout into the worktree (do not invent a second YAML system).

- [ ] **Step 2: Commit foundation only if it was uncommitted**

```bash
git add saads_grill_agent/runtime_config.py saads_grill_agent/contracts.py saads_grill_agent/__main__.py red-team-config.yaml tests/saads_grill_agent/test_runtime_config.py tests/saads_grill_agent/test_cli.py
# plus any other files strictly required for YAML config tests to pass
git commit -m "chore: land red-team YAML config foundation for grill"
```

Skip the commit if foundation is already on the branch.

---

### Task 1: `use_graphrag` config + `AssessmentConfig` field

**Files:**
- Modify: `saads_grill_agent/contracts.py`
- Modify: `saads_grill_agent/runtime_config.py`
- Modify: `red-team-config.yaml`
- Modify: `tests/saads_grill_agent/test_runtime_config.py`
- Test: `tests/saads_grill_agent/test_runtime_config.py`

**Interfaces:**
- Produces: `RedTeamConfig.use_graphrag: bool = True`, `AssessmentConfig.use_graphrag: bool = True`, `merge_cli_over_config(..., use_graphrag: bool | None = None)` where `False` forces off; `None` leaves unchanged. `to_assessment_config` copies the flag.

- [ ] **Step 1: Write failing tests**

```python
def test_use_graphrag_defaults_true() -> None:
    assert RedTeamConfig().use_graphrag is True
    assert default_red_team_config().to_assessment_config(Path("t")).use_graphrag is True


def test_yaml_can_disable_use_graphrag(tmp_path: Path) -> None:
    path = tmp_path / "c.yaml"
    path.write_text("use_graphrag: false\n", encoding="utf-8")
    assert load_red_team_config(path).use_graphrag is False


def test_merge_cli_no_graphrag_forces_false() -> None:
    cfg = RedTeamConfig(use_graphrag=True)
    merged = merge_cli_over_config(
        cfg,
        target_repo=None,
        authorization_ref=None,
        goal=None,
        output_root=None,
        max_rounds=None,
        max_cost_usd=None,
        use_graphrag=False,
    )
    assert merged.use_graphrag is False
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `uv run pytest tests/saads_grill_agent/test_runtime_config.py -q -k use_graphrag`

- [ ] **Step 3: Implement fields + merge + YAML comment**

Add `use_graphrag: bool = True` to `RedTeamConfig` and `AssessmentConfig`. Extend `merge_cli_over_config` with `use_graphrag: bool | None = None` (`if use_graphrag is False: updates["use_graphrag"] = False`). Pass through `to_assessment_config`. Add commented key to `red-team-config.yaml`.

- [ ] **Step 4: Run tests — expect PASS**

Run: `uv run pytest tests/saads_grill_agent/test_runtime_config.py -q`

- [ ] **Step 5: Commit**

```bash
git add saads_grill_agent/contracts.py saads_grill_agent/runtime_config.py red-team-config.yaml tests/saads_grill_agent/test_runtime_config.py
git commit -m "feat(grill): add use_graphrag config flag"
```

---

### Task 2: Graph index probe + runtime resolution helper

**Files:**
- Create: `saads_grill_agent/graph_runtime.py`
- Create: `tests/saads_grill_agent/test_graph_runtime.py`

**Interfaces:**
- Consumes: `saads_attack_agent.security_graph.REQUIRED_TABLES` (or duplicate the five names to avoid tight coupling — prefer import of `REQUIRED_TABLES` if exported; else local tuple matching security_graph)
- Produces:

```python
@dataclass(frozen=True)
class GraphRuntime:
    enabled: bool
    skipped_reason: str | None  # None | disabled_by_config | index_unavailable | index_load_failed
    graph: SecurityGraph | None

def probe_graph_index(root: Path) -> bool: ...
def resolve_graph_runtime(*, root: Path, use_graphrag: bool) -> GraphRuntime: ...
```

Rules: if not `use_graphrag` → enabled False, reason `disabled_by_config`, no load. If probe fails → `index_unavailable`, no load. If probe ok but `SecurityGraph.load` raises → `index_load_failed`. Else enabled True, graph set, reason None.

- [ ] **Step 1: Write failing tests** using `tmp_path` fixtures (no real parquet needed for unavailable; for available, create empty placeholder files named correctly — probe only checks `is_file()`, load path is tested with monkeypatch)

```python
def test_probe_false_when_missing(tmp_path: Path) -> None:
    assert probe_graph_index(tmp_path) is False

def test_probe_true_when_settings_and_tables_exist(tmp_path: Path) -> None:
    (tmp_path / "settings.yaml").write_text("x: 1\n", encoding="utf-8")
    out = tmp_path / "output"
    out.mkdir()
    for name in ("entities", "communities", "community_reports", "text_units", "relationships"):
        (out / f"{name}.parquet").write_bytes(b"x")
    assert probe_graph_index(tmp_path) is True

def test_resolve_disabled_by_config(tmp_path: Path) -> None:
    rt = resolve_graph_runtime(root=tmp_path, use_graphrag=False)
    assert rt.enabled is False and rt.skipped_reason == "disabled_by_config" and rt.graph is None

def test_resolve_index_unavailable(tmp_path: Path) -> None:
    rt = resolve_graph_runtime(root=tmp_path, use_graphrag=True)
    assert rt.skipped_reason == "index_unavailable"

def test_resolve_load_failure(monkeypatch, tmp_path: Path) -> None:
    # make probe pass, load raise
    ...
    assert rt.skipped_reason == "index_load_failed"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/saads_grill_agent/test_graph_runtime.py -q`

- [ ] **Step 3: Implement `graph_runtime.py`**

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add saads_grill_agent/graph_runtime.py tests/saads_grill_agent/test_graph_runtime.py
git commit -m "feat(grill): probe GraphRAG index before load"
```

---

### Task 3: CLI `--no-graphrag` + optional load in `run_live_assessment`

**Files:**
- Modify: `saads_grill_agent/__main__.py`
- Modify: `tests/saads_grill_agent/test_cli.py`

**Interfaces:**
- Consumes: `resolve_graph_runtime`, `RedTeamConfig.use_graphrag`
- Produces: `--no-graphrag` on start/resume; merge forces false; `run_live_assessment` uses `GraphRuntime` — MCP `security_graph` only if enabled; pass `graph_enabled` into `TeamBackend` / orchestrator; write `use_graphrag`, `graph_enabled`, `graph_skipped_reason` into `red-team-config.resolved.yaml`; stderr info line when skipped (optional); missing index must not raise `GraphConfigurationError` to CLI.

- [ ] **Step 1: Failing CLI tests**

```python
def test_start_no_graphrag_flag_merges_false(tmp_path: Path) -> None:
    # prepare minimal config yaml with use_graphrag true + target/auth
    # parse/merge path or invoke _prepare_start with argv including --no-graphrag
    assert context.config.use_graphrag is False

def test_run_live_assessment_skips_load_when_index_missing(monkeypatch, tmp_path: Path) -> None:
    # monkeypatch SecurityGraph.load to raise if called; resolve path with empty root
    # assert load not called and assessment runner proceeds (mock orchestrator)
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/saads_grill_agent/test_cli.py -q -k graphrag`

- [ ] **Step 3: Wire CLI + `run_live_assessment`**

Replace unconditional `SecurityGraph.load` with `resolve_graph_runtime(root=PROJECT_ROOT, use_graphrag=context.config.use_graphrag)`.

- [ ] **Step 4: Run grill CLI tests**

Run: `uv run pytest tests/saads_grill_agent/test_cli.py -q`

- [ ] **Step 5: Commit**

```bash
git add saads_grill_agent/__main__.py tests/saads_grill_agent/test_cli.py
git commit -m "feat(grill): optional GraphRAG load and --no-graphrag"
```

---

### Task 4: `TeamBackend` cwd / Skill / tool gating

**Files:**
- Modify: `saads_grill_agent/teams.py`
- Modify: `tests/saads_grill_agent/test_teams.py`

**Interfaces:**
- Produces: `TeamBackend(..., project_root: Path, graph_enabled: bool = False)`
- When building options:
  - `cwd=str(project_root)` always
  - if `graph_enabled` and role in `{red_team, judge}`: `setting_sources=["project"]`, `skills=["ground-red-team-evidence"]`, include `"Skill"` and `GRAPH_TOOL` in allowed tools
  - if not `graph_enabled`: no Skill, no `GRAPH_TOOL`, `setting_sources=[]`, omit `graph-grounder`; `test-strategist` repo-only tools
  - code_team never gets graph tools/skill
  - MCP servers dict may omit `security_graph` (caller responsibility); backend must not reference graph tool if disabled

- [ ] **Step 1: Failing tests** inspecting `_build_options` / `_role_tools` / `_role_agents`

```python
def test_red_tools_include_graph_when_enabled(...): ...
def test_red_tools_exclude_graph_when_disabled(...): ...
def test_cwd_is_project_root(...): ...
def test_skills_loaded_only_when_graph_enabled(...): ...
def test_graph_grounder_absent_when_disabled(...): ...
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run pytest tests/saads_grill_agent/test_teams.py -q`

- [ ] **Step 3: Implement gating** (keep DeepSeek env / hooks / structured output as today)

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add saads_grill_agent/teams.py tests/saads_grill_agent/test_teams.py
git commit -m "feat(grill): gate GraphRAG tools and project Skill in TeamBackend"
```

---

### Task 5: Skill file + orchestrator prompt tweaks

**Files:**
- Create: `.claude/skills/ground-red-team-evidence/SKILL.md`
- Modify: `saads_grill_agent/orchestrator.py`
- Modify: `tests/saads_grill_agent/test_orchestrator.py` (assert prompt fragments when graph_enabled; use a fake backend that records prompts)

**Interfaces:**
- Orchestrator receives `graph_enabled: bool` (constructor or from config + runtime flag stored on orchestrator at run start).
- Prompt helpers append grilling bullets always (short); append `$ground-red-team-evidence` sentence only if `graph_enabled`.

Skill frontmatter:

```yaml
---
name: ground-red-team-evidence
description: Ground red-team or judge claims in optional project GraphRAG evidence. Use when proposing or refining LLM vulnerability hypotheses, adjudicating, or needing attack-mechanism / control background from the security graph.
---
```

Body: purpose map (`threat_modeling`, `hypothesis_grounding`, `adjudication_grounding`, `test_grounding`), call `mcp__security_graph__query_security_graph`, cite `evidence_id`, optional/no padding, offline boundary.

- [ ] **Step 1: Write Skill file + failing prompt assertion tests**

- [ ] **Step 2: Run orchestrator tests — expect FAIL on new assertions**

- [ ] **Step 3: Wire prompt appendices; do not change loop/convergence logic**

- [ ] **Step 4: Run**

Run: `uv run pytest tests/saads_grill_agent/test_orchestrator.py tests/saads_grill_agent/test_skills.py -q`  
(If `test_skills.py` does not exist, add a tiny test that the Skill path exists and name matches.)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ground-red-team-evidence/SKILL.md saads_grill_agent/orchestrator.py tests/saads_grill_agent/test_orchestrator.py tests/saads_grill_agent/test_skills.py
git commit -m "feat(grill): add ground-red-team-evidence Skill and soft prompts"
```

---

### Task 6: Report blurb + README + full regression

**Files:**
- Modify: `saads_grill_agent/report.py`
- Modify: `README.md` (grill section only)
- Modify: tests for report if present

**Interfaces:**
- `write_reports` / markdown renderer reads `state.config.use_graphrag` plus optional runtime fields. Prefer storing `graph_enabled` / `graph_skipped_reason` on `AssessmentState` if easy; else pass via config extension fields on state at run start:

```python
# On AssessmentState or a small sidecar written into state before report:
graph_enabled: bool = False
graph_skipped_reason: str | None = None
```

If adding to `AssessmentState`, keep Pydantic defaults so old ledgers resume.

- [ ] **Step 1: Report includes a short「知识接地」section**

- [ ] **Step 2: README note** — optional GraphRAG, `--no-graphrag`, auto-degrade without index

- [ ] **Step 3: Full package tests**

Run: `uv run pytest tests/saads_grill_agent -q`  
Run: `uv run python -m compileall -q saads_grill_agent`

- [ ] **Step 4: Commit**

```bash
git add saads_grill_agent/report.py saads_grill_agent/contracts.py README.md tests/saads_grill_agent
git commit -m "docs(grill): report GraphRAG status and README note"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|---|---|
| `use_graphrag` YAML + `--no-graphrag` | 1, 3 |
| Probe-then-load / no fail on missing index | 2, 3 |
| Skill `ground-red-team-evidence` | 5 |
| Soft prompt guidance + grilling short lines | 5 |
| Tool/MCP/Skill gating | 4 |
| cwd = PROJECT_ROOT | 4 |
| Resolved YAML fields | 3 |
| Report visibility | 6 |
| Attack agent untouched | all |
| No state-machine rewrite | 5 |

## Execution notes

- Work on an isolated git worktree / feature branch — not dirty `main` WIP mixed with unrelated deletes.
- Subagent models: only `cursor-grok-4.5-high-fast` or `composer-2.5-fast`.
- After all tasks: run finishing-a-development-branch.
