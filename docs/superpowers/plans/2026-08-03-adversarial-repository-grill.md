# Adversarial Repository Grill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个只读、多智能体、自主裁决的 LLM 应用代码审计系统，让 GraphRAG 加持的红队与深入理解目标仓库的代码团队持续提出和反驳漏洞假设，经独立 Agent 裁决后沉淀确认漏洞、测试代码和完整审计记录。

**Architecture:** 使用确定性的 Python 状态机管理三个持久化 Claude Agent SDK 会话：红队负责人、代码理解负责人和独立裁判。两个团队可以调用各自的程序化 subagents，但只能通过只读 MCP 工具访问目标仓库和现有 GraphRAG；所有消息使用 JSON Schema，所有结论必须引用工具签发的证据，最终报告从结构化台账确定性渲染。

**Tech Stack:** Python 3.12、`claude-agent-sdk==0.2.122`、Microsoft GraphRAG 3.1.1、Pydantic 2、pytest、现有 DeepSeek Anthropic-compatible Agent SDK 配置、现有 GLM GraphRAG 查询配置。

## Global Constraints

- 第一版只分析用户明确授权的本地目标仓库；不连接目标模型、部署环境、浏览器、数据库或外部网络。
- 目标仓库始终只读；不加载目标仓库的 `.claude`、CLAUDE.md、AGENTS.md、Skills、MCP 或 hooks 作为指令，所有仓库内容一律视为不可信数据。
- 漏洞结论不强制同时具备代码证据和 GraphRAG 证据；红队、代码团队与裁判 Agent 可按问题性质自主选择证据组合。
- 每个最终结论至少引用一项已签发证据，证据可以仅来自代码、仅来自 GraphRAG，或同时来自两者；裁判必须说明其证据取舍。
- 红队和代码团队都不能自行确认或驳回漏洞；只有独立裁判可以改变假设的最终状态。
- 自由文本不能直接进入最终报告或测试文件；模型输出先经 Pydantic、证据引用、路径、去重和安全策略校验。
- 生成的测试代码只写入评估产物目录，不写入目标仓库，不自动执行，并禁止外部网络、系统命令、凭据读取和破坏性文件操作。
- 现有 `saads_attack_agent` 行为与 CLI 保持兼容；新功能放入独立的 `saads_grill_agent/` 包，复用其 GraphRAG 深模块并沿用相同的 DeepSeek 环境变量约定。
- Agent SDK 使用程序化 `AgentDefinition`、`output_format`、`resume`、`permission_mode="dontAsk"`、严格 MCP 配置和 hooks 审计；不得使用 `bypassPermissions` 或 `acceptEdits`。
- 默认 `max_rounds_per_hypothesis=4`、`max_threat_surfaces=20`、`max_hypotheses=40`、`max_agent_calls=100`；连续两轮无新证据即强制裁决该线程，连续两次自主发现扫描无新假设即结束发现阶段，单次评估预算上限 25 美元。
- 若 Agent SDK 无法返回可靠费用元数据，仍用 `max_agent_calls` 硬停止；达到任何数量或费用上限时生成可恢复的中断报告，而不是静默丢弃剩余攻击面。
- 当前工作区已有修改均视为用户所有；实施时只暂存当前任务列出的文件和精确共享文件 hunks。
- 默认测试不得调用付费模型或真实 GraphRAG completion；一次显式 live acceptance 在离线测试通过后执行。

## Chosen Design

- 不采用两个自由对话 Agent 直接互聊：该方案无法可靠去重、终止、审计或阻止双方在无证据时达成共识。
- 不采用单 Agent 轮换“红队/蓝队”人格：上下文共享会削弱真正的反证压力，也无法隔离工具与提示。
- 采用“两个持久团队会话 + 独立裁判 + 确定性状态机”：会话保留上下文，subagents 提供专业分工，状态机控制轮次和预算，裁判只根据签发证据定案。

## File Structure

- `saads_grill_agent/contracts.py`：评估、仓库画像、证据、假设、辩论、裁决、漏洞和测试产物契约。
- `saads_grill_agent/repository.py`：目标仓库快照、路径隔离、代码检索/片段读取、证据哈希和只读 MCP 工具。
- `saads_grill_agent/teams.py`：三个角色的 Agent SDK 配置、程序化 subagents、结构化单轮调用和 session resume。
- `saads_grill_agent/orchestrator.py`：画像、发现、辩论、自动裁决、发现收敛和测试生成状态机。
- `saads_grill_agent/ledger.py`：原子保存运行状态、事件、证据、假设、辩论轮次、漏洞和 session IDs。
- `saads_grill_agent/test_artifacts.py`：生成测试代码的策略校验与产物写入。
- `saads_grill_agent/report.py`：从台账确定性生成 Markdown/JSON 报告。
- `saads_grill_agent/__main__.py`：创建、恢复评估的 CLI。
- `tests/saads_grill_agent/`：所有新模块的离线行为测试与脆弱目标仓库 fixture。

---

### Task 1: Define the assessment contracts and state transitions

**Files:**
- Create: `saads_grill_agent/__init__.py`
- Create: `saads_grill_agent/contracts.py`
- Create: `tests/saads_grill_agent/test_contracts.py`

**Interfaces:**
- Produces: `AssessmentConfig`, `RepositoryProfile`, `ThreatSurface`, `CodeEvidence`, `VulnerabilityHypothesis`, `DefenderRebuttal`, `RedResponse`, `Adjudication`, `Finding`, `GeneratedTestDraft`, `AssessmentState`.
- Consumes: Python standard library and Pydantic only.

- [ ] **Step 1: Write failing transition tests**

```python
def test_only_adjudication_can_finalize_a_hypothesis() -> None:
    hypothesis = vulnerability_hypothesis()
    with pytest.raises(ValidationError, match="adjudication"):
        HypothesisRecord(
            hypothesis=hypothesis,
            status="confirmed",
            final_adjudication_id=None,
        )


def test_confirmed_finding_accepts_either_code_or_graph_evidence() -> None:
    finding = Finding.model_validate({
        **valid_finding_dict(),
        "code_evidence_ids": ["code-1"],
        "graph_evidence_ids": [],
    })
    assert finding.code_evidence_ids == ["code-1"]


def test_confirmed_finding_rejects_an_evidence_free_decision() -> None:
    with pytest.raises(ValidationError, match="at least one signed evidence"):
        Finding.model_validate({
            **valid_finding_dict(),
            "code_evidence_ids": [],
            "graph_evidence_ids": [],
        })
```

- [ ] **Step 2: Run the contract tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_contracts.py -q`

Expected: collection fails because `saads_grill_agent.contracts` does not exist.

- [ ] **Step 3: Implement exact status and message types**

```python
HypothesisStatus = Literal[
    "proposed", "debating", "confirmed", "rejected", "duplicate",
]
AdjudicationVerdict = Literal[
    "confirm", "reject", "request_more_evidence", "duplicate",
]
GraphReviewPurpose = Literal[
    "threat_modeling", "hypothesis_grounding",
    "adjudication_grounding", "test_grounding",
]

class AssessmentConfig(ContractModel):
    target_repo: Path
    goal: str = "审查该 LLM 应用的代码级安全漏洞"
    supplied_model_provider: str | None = None
    supplied_model_name: str | None = None
    supplied_agent_framework: str | None = None
    supplied_frontend_roots: list[str] = Field(default_factory=list)
    supplied_backend_roots: list[str] = Field(default_factory=list)
    scope_includes: list[str] = Field(default_factory=list)
    scope_excludes: list[str] = Field(default_factory=list)
    max_rounds_per_hypothesis: int = Field(default=4, ge=1, le=6)
    max_threat_surfaces: int = Field(default=20, ge=1, le=50)
    max_hypotheses: int = Field(default=40, ge=1, le=100)
    max_agent_calls: int = Field(default=100, ge=5, le=250)
    max_cost_usd: float = Field(default=25.0, gt=0, le=100)

class RepositoryProfile(ContractModel):
    snapshot_id: str
    model_provider: str
    model_name: str
    agent_framework: str
    frontend_roots: list[str]
    backend_roots: list[str]
    model_call_sites: list[str]
    prompt_assembly_sites: list[str]
    tool_definition_sites: list[str]
    retrieval_and_ingestion_sites: list[str]
    memory_sites: list[str]
    authn_authz_sites: list[str]
    output_interpretation_sites: list[str]
    test_frameworks: list[Literal["pytest", "vitest", "jest"]]
    profile_evidence_ids: list[str] = Field(min_length=1)
    supplied_profile_conflicts: list[str]

class ThreatSurface(ContractModel):
    surface_id: str
    kind: Literal[
        "prompt_boundary", "rag_ingestion", "rag_retrieval", "memory",
        "tool_call", "model_output", "frontend", "backend",
        "identity_authorization", "secret_config", "supply_chain",
    ]
    name: str
    entrypoints: list[str] = Field(min_length=1)
    trust_transition: str
    assets: list[str] = Field(min_length=1)
    code_evidence_ids: list[str] = Field(min_length=1)

class CodeEvidence(ContractModel):
    evidence_id: str
    relative_path: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    excerpt: str = Field(min_length=1, max_length=4000)
    claim: str = Field(min_length=1)

class VulnerabilityHypothesis(ContractModel):
    hypothesis_id: str
    surface_id: str
    title: str
    root_cause: str
    attack_path: list[str] = Field(min_length=1)
    impact: str
    preconditions: list[str]
    code_evidence_ids: list[str] = Field(default_factory=list)
    graph_evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_one_autonomous_evidence_source(self) -> "VulnerabilityHypothesis":
        if not self.code_evidence_ids and not self.graph_evidence_ids:
            raise ValueError("hypothesis requires at least one signed evidence")
        return self

class HypothesisRecord(ContractModel):
    hypothesis: VulnerabilityHypothesis
    status: HypothesisStatus
    final_adjudication_id: str | None

    @model_validator(mode="after")
    def require_adjudication_for_terminal_status(self) -> "HypothesisRecord":
        terminal = {"confirmed", "rejected", "duplicate"}
        if self.status in terminal and not self.final_adjudication_id:
            raise ValueError("terminal hypothesis status requires adjudication")
        return self

class DefenderRebuttal(ContractModel):
    hypothesis_id: str
    round_number: int = Field(ge=1)
    disposition: Literal["refute", "mitigated", "unreachable", "concede", "insufficient_evidence"]
    arguments: list[str] = Field(min_length=1)
    new_code_evidence_ids: list[str]
    unresolved_conditions: list[str]

class RedResponse(ContractModel):
    hypothesis_id: str
    round_number: int = Field(ge=1)
    disposition: Literal["withdraw", "refine", "stand"]
    reasoning: list[str] = Field(min_length=1)
    revised_hypothesis: VulnerabilityHypothesis | None
    new_code_evidence_ids: list[str]
    new_graph_evidence_ids: list[str]

class Adjudication(ContractModel):
    hypothesis_id: str
    round_number: int = Field(ge=1)
    verdict: AdjudicationVerdict
    rationale: list[str] = Field(min_length=1)
    accepted_code_evidence_ids: list[str]
    accepted_graph_evidence_ids: list[str]
    missing_proof: list[str]
    duplicate_of: str | None
    confidence: float = Field(ge=0.0, le=1.0)
```

`Finding` must include `finding_id`, `hypothesis_id`, severity (`critical/high/medium/low`), confidence (`high/medium/low`), root cause, reachable attack path, impact, preconditions, accepted evidence IDs, remediation, and generated test IDs. `AssessmentState.hypotheses` stores `HypothesisRecord` values, and `AssessmentState.apply_adjudication()` is the only orchestration method that creates a terminal record and validates that every referenced evidence ID exists in the ledger.

When a supplied model/framework/path conflicts with code evidence, preserve both values in `RepositoryProfile.supplied_profile_conflicts`; do not silently prefer either. The code team must resolve the conflict with additional evidence or the judge selects one interpretation and records its rationale in the internal event log.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_contracts.py -q`

Expected: invalid transitions fail and fully evidenced transitions pass.

- [ ] **Step 5: Commit Task 1**

```powershell
git add -- saads_grill_agent/__init__.py saads_grill_agent/contracts.py tests/saads_grill_agent/test_contracts.py
git commit -m "feat: define adversarial review contracts"
```

---

### Task 2: Build the read-only repository evidence module

**Files:**
- Create: `saads_grill_agent/repository.py`
- Create: `tests/saads_grill_agent/test_repository.py`

**Interfaces:**
- Produces: `RepositoryEvidenceStore.open(root)`, `inventory()`, `search()`, `read_snippet()`, and `create_repository_server()`.
- Consumes: a resolved local repository path; returns signed `CodeEvidence` only.

- [ ] **Step 1: Write failing isolation and evidence tests**

```python
def test_read_snippet_signs_exact_lines_and_rejects_escape(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"app/main.py": "a = 1\nsecret = source()\nsink(secret)\n"})
    store = RepositoryEvidenceStore.open(repo)

    evidence = store.read_snippet("app/main.py", 2, 3, "Untrusted value reaches sink")

    assert evidence.relative_path == "app/main.py"
    assert evidence.excerpt == "secret = source()\nsink(secret)"
    assert len(evidence.content_sha256) == 64
    with pytest.raises(RepositoryAccessError):
        store.read_snippet("../outside.txt", 1, 1, "escape")
```

Add tests for symlinks escaping the root, binary files, files over 2 MiB, ignored directories (`.git`, `.venv`, `node_modules`, `dist`, `build`), maximum 200 search matches, and secret redaction for common API-key assignments.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_repository.py -q`

Expected: import fails because `repository.py` does not exist.

- [ ] **Step 3: Implement the deep repository interface**

`RepositoryEvidenceStore` resolves every requested path with `Path.resolve()`, verifies `candidate.is_relative_to(root)`, rejects escaping symlinks, reads UTF-8 text only, and signs evidence as:

```python
raw_sha256 = sha256(raw_excerpt.encode("utf-8")).hexdigest()
digest_input = f"{snapshot_id}\0{relative_path}\0{line_start}\0{line_end}\0{raw_sha256}"
content_sha256 = raw_sha256
evidence_id = "code-" + sha256(digest_input.encode("utf-8")).hexdigest()[:16]
```

`raw_excerpt` never leaves the module before secret redaction; `CodeEvidence.excerpt` stores the redacted text while `content_sha256` signs the original bytes. `inventory()` returns `snapshot_id`, git HEAD when available, file count, language counts, detected test manifests, and a manifest digest. It never executes target code. `search()` performs literal/regex search inside the validated file set and returns path, line, and preview records; only `read_snippet()` creates citable evidence.

- [ ] **Step 4: Expose three in-process MCP tools**

Create `list_repository`, `search_repository`, and `read_repository_snippet` with full JSON Schemas, `ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)`, and an injected evidence audit list. Tool handlers return `is_error=True` for validation failures and never expose absolute paths.

- [ ] **Step 5: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_repository.py -q`

Expected: path isolation, evidence signing, caps and MCP audit tests pass.

- [ ] **Step 6: Commit Task 2**

```powershell
git add -- saads_grill_agent/repository.py tests/saads_grill_agent/test_repository.py
git commit -m "feat: add read-only repository evidence tools"
```

---

### Task 3: Extend GraphRAG evidence purposes without breaking the existing agent

**Files:**
- Modify: `saads_attack_agent/contracts.py`
- Modify: `saads_attack_agent/security_graph.py`
- Modify: `tests/saads_attack_agent/test_contracts.py`
- Modify: `tests/saads_attack_agent/test_security_graph.py`

**Interfaces:**
- Preserves: `SecurityGraph.query(purpose, question) -> GraphEvidence` and all existing three attack-case purposes.
- Adds: `threat_modeling`, `hypothesis_grounding`, `adjudication_grounding`, `test_grounding`.

- [ ] **Step 1: Add a failing compatibility test**

```python
@pytest.mark.parametrize("purpose", [
    "intent_classification", "case_grounding", "script_grounding",
    "threat_modeling", "hypothesis_grounding",
    "adjudication_grounding", "test_grounding",
])
def test_security_graph_accepts_all_audited_purposes(purpose: str) -> None:
    evidence = asyncio.run(stub_graph().query(purpose, "ground this claim"))
    assert evidence.purpose == purpose
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `uv run pytest tests/saads_attack_agent/test_contracts.py tests/saads_attack_agent/test_security_graph.py -q`

Expected: the four review purposes fail Pydantic or query validation.

- [ ] **Step 3: Extend only the literal and MCP enum**

Add the four strings to `QueryPurpose` and `QUERY_PURPOSES`. Do not change local-search parameters, existing evidence hashing, required purposes in `AttackCaseAgent`, or existing CLI behavior. The review system uses:

- `threat_modeling` for attack-surface mapping;
- `hypothesis_grounding` for proposing mechanisms and controls;
- `adjudication_grounding` for checking disputed security claims;
- `test_grounding` for safe reproducer design.

- [ ] **Step 4: Run existing and new tests**

Run: `uv run pytest tests/saads_attack_agent -q`

Expected: all existing attack-agent tests and new purpose cases pass.

- [ ] **Step 5: Commit Task 3**

```powershell
git add -- saads_attack_agent/contracts.py saads_attack_agent/security_graph.py tests/saads_attack_agent/test_contracts.py tests/saads_attack_agent/test_security_graph.py
git commit -m "feat: add repository review graph purposes"
```

---

### Task 4: Implement persistent team sessions with programmatic subagents

**Files:**
- Create: `saads_grill_agent/teams.py`
- Create: `tests/saads_grill_agent/test_teams.py`

**Interfaces:**
- Produces: `TeamBackend.run_turn(role, prompt, output_model, session_id, audits) -> TeamTurnResult[OutputModel]`.
- Consumes: repository MCP server, GraphRAG MCP server, a role, structured-output model and optional prior session ID.

- [ ] **Step 1: Write failing SDK option tests with a fake query stream**

```python
def test_red_team_gets_only_agent_and_read_only_mcp_tools(tmp_path: Path) -> None:
    backend, captured = fake_team_backend(tmp_path, valid_hypothesis_batch())
    result = asyncio.run(backend.run_turn(
        role="red_team",
        prompt="Discover grounded hypotheses",
        output_model=HypothesisBatch,
        session_id="session-red-1",
        audits=empty_audits(),
    ))

    options = captured.options
    assert options.resume == "session-red-1"
    assert options.setting_sources == []
    assert options.permission_mode == "dontAsk"
    assert set(options.allowed_tools) == {
        "Agent",
        "mcp__repository__list_repository",
        "mcp__repository__search_repository",
        "mcp__repository__read_repository_snippet",
        "mcp__security_graph__query_security_graph",
    }
    assert "Bash" not in options.tools
    assert result.session_id == "session-from-result"
```

Add separate tests showing the code team cannot call GraphRAG, the judge cannot invoke subagents, every call uses `output_format`, failures keep the previous state unchanged, and `PreToolUse`/`PostToolUse` hooks append auditable tool events.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_teams.py -q`

Expected: import fails because `teams.py` does not exist.

- [ ] **Step 3: Define programmatic teams**

Use `AgentDefinition` exactly as follows:

```python
RED_SUBAGENTS = {
    "graph-grounder": AgentDefinition(
        description="Grounds one LLM attack mechanism and known controls in GraphRAG.",
        prompt=RED_GRAPH_PROMPT,
        tools=["mcp__security_graph__query_security_graph"],
        permissionMode="dontAsk",
    ),
    "attack-path-analyst": AgentDefinition(
        description="Traces one proposed source-to-sink attack path in repository evidence.",
        prompt=ATTACK_PATH_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
    "test-strategist": AgentDefinition(
        description="Designs a non-executing repository-native regression test for a confirmed finding.",
        prompt=TEST_STRATEGIST_PROMPT,
        tools=REPOSITORY_TOOLS + [GRAPH_TOOL],
        permissionMode="dontAsk",
    ),
}

CODE_SUBAGENTS = {
    "architecture-mapper": AgentDefinition(
        description="Maps model, agent, RAG, tool, frontend and backend trust seams from code evidence.",
        prompt=ARCHITECTURE_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
    "reachability-falsifier": AgentDefinition(
        description="Attempts to prove a proposed attack path unreachable using code evidence.",
        prompt=REACHABILITY_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
    "control-verifier": AgentDefinition(
        description="Searches for concrete validation, authorization, isolation and approval controls.",
        prompt=CONTROL_PROMPT,
        tools=REPOSITORY_TOOLS,
        permissionMode="dontAsk",
    ),
}
```

The red lead autonomously decides whether to consult `graph-grounder`, `attack-path-analyst` or both for each hypothesis. The code lead likewise decides whether it needs `reachability-falsifier`, `control-verifier` or direct repository inspection. The judge receives both evidence tools but no `Agent` tool and no subagents, and may accept either evidence family when its rationale explains why that evidence is sufficient.

- [ ] **Step 4: Implement session resume and structured output**

Each `run_turn()` call uses a new `query()` invocation with `resume=session_id` when present, captures `ResultMessage.session_id`, validates `structured_output` through `output_model.model_validate`, and returns token/cost metadata. Keep `cwd` fixed to the resolved target repository for every resumed session. Set `max_turns=12`, `max_budget_usd=1.50` for team turns and `0.75` for judge turns.

- [ ] **Step 5: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_teams.py -q`

Expected: role isolation, subagent definitions, resume, structured output and hook audit tests pass.

- [ ] **Step 6: Commit Task 4**

```powershell
git add -- saads_grill_agent/teams.py tests/saads_grill_agent/test_teams.py
git commit -m "feat: add persistent adversarial review teams"
```

---

### Task 5: Implement the evidence-driven grill state machine

**Files:**
- Create: `saads_grill_agent/orchestrator.py`
- Create: `tests/saads_grill_agent/test_orchestrator.py`

**Interfaces:**
- Produces: `AssessmentOrchestrator.run(config) -> AssessmentState` and `resume(state) -> AssessmentState`.
- Consumes: `TeamBackend`, `RepositoryEvidenceStore`, `SecurityGraph`, `AssessmentLedger`.

- [ ] **Step 1: Write failing end-to-end state tests using scripted teams**

```python
def test_debate_confirms_only_after_rebuttal_red_response_and_judgment() -> None:
    backend = ScriptedTeamBackend([
        repository_profile_with_two_surfaces(),
        hypothesis_batch([prompt_injection_hypothesis()]),
        rebuttal(disposition="mitigated", evidence=[partial_filter_evidence()]),
        red_response(disposition="stand", evidence=[filter_bypass_evidence()]),
        adjudication(verdict="confirm"),
        hypothesis_batch([]),
        hypothesis_batch([]),
        generated_test_draft(),
    ])

    state = asyncio.run(make_orchestrator(backend).run(default_config()))

    assert [f.hypothesis_id for f in state.findings] == ["hyp-pi-1"]
    assert state.hypotheses["hyp-pi-1"].status == "confirmed"
    assert state.discovery.consecutive_empty_sweeps == 2
    assert backend.role_order == [
        "code_team", "red_team", "code_team", "red_team", "judge",
        "red_team", "red_team", "red_team",
    ]
```

Add tests for red withdrawal, judge rejection, duplicate detection, four-round cap, two rounds without new evidence, 20-surface/40-hypothesis/100-call caps, global 25-dollar cap, missing cost metadata, interrupted-run resume, and repository snapshot mismatch on resume.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_orchestrator.py -q`

Expected: import fails because `orchestrator.py` does not exist.

- [ ] **Step 3: Implement the exact phase sequence**

```text
intake -> repository_profile -> autonomous_discovery_queue
       -> red_discovery -> deduplicate
       -> defender_rebuttal -> red_response -> adjudication
       -> repeat thread or finalize
       -> discovery_sweep until two consecutive empty sweeps
       -> generate_test_drafts for confirmed findings
       -> complete
```

Repository profiling must identify model calls, system prompts, agent framework, tool definitions, RAG ingestion/retrieval, memory, authn/authz, frontend input handling, backend output handling, secrets/config and test framework. Every `ThreatSurface` requires at least one `CodeEvidence` reference.

For each hypothesis round:

1. Code team attempts the strongest concrete falsification it can establish from the repository.
2. Red team may withdraw, refine or stand, and autonomously decides whether new code or GraphRAG queries are useful.
3. Judge checks that every referenced evidence ID was actually issued, then weighs code evidence, GraphRAG evidence and the teams' structured reasoning without imposing a fixed evidence mix.
4. `confirm` requires the judge to find the vulnerability more likely than not, identify a plausible attack path and cite at least one signed code or GraphRAG evidence item.
5. `reject` is valid when the claim is contradicted, unreachable, effectively mitigated or remains too speculative after the permitted rounds; it also cites at least one signed evidence item.
6. `request_more_evidence` is non-terminal and is allowed only before the final round. At the fourth round the judge must choose `confirm`, `reject` or `duplicate` and attach a confidence score.

- [ ] **Step 4: Implement convergence and deduplication**

Compute `hypothesis_id` from normalized `(surface_id, root_cause, source_path, sink_path)` rather than model wording. Stop a thread when finalized. If the union of evidence IDs does not change for two rounds, immediately ask the judge for a forced final decision. End discovery after two consecutive autonomous red-team sweeps return no new unique hypothesis.

When any resource cap is reached, checkpoint all sessions and evidence, finalize every active hypothesis through the judge, render the findings obtained so far, and record the internal termination reason only in `run_state.json` and `events.jsonl`. The user-facing vulnerability report does not add scope, coverage or resource-limit sections.

- [ ] **Step 5: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_orchestrator.py -q`

Expected: all terminal states, budgets, convergence and resume cases pass.

- [ ] **Step 6: Commit Task 5**

```powershell
git add -- saads_grill_agent/orchestrator.py tests/saads_grill_agent/test_orchestrator.py
git commit -m "feat: orchestrate evidence-driven grill debates"
```

---

### Task 6: Persist an append-only audit ledger

**Files:**
- Create: `saads_grill_agent/ledger.py`
- Create: `tests/saads_grill_agent/test_ledger.py`

**Interfaces:**
- Produces: `AssessmentLedger.create()`, `append_event()`, `checkpoint()`, and `load()`.
- Consumes: validated contract objects only.

- [ ] **Step 1: Write failing crash-safety tests**

```python
def test_checkpoint_is_atomic_and_event_log_is_append_only(tmp_path: Path) -> None:
    ledger = AssessmentLedger.create(tmp_path, initial_state())
    ledger.append_event(valid_debate_event())
    ledger.checkpoint(updated_state())

    assert json.loads((tmp_path / "run_state.json").read_text("utf-8"))["phase"] == "debating"
    assert len((tmp_path / "events.jsonl").read_text("utf-8").splitlines()) == 1
    assert not list(tmp_path.glob("*.tmp"))
```

Add tests for invalid JSONL tail recovery, incompatible schema version, target snapshot mismatch and restoration of red/code/judge session IDs.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_ledger.py -q`

Expected: import fails because `ledger.py` does not exist.

- [ ] **Step 3: Implement the artifact layout**

```text
<run-dir>/
  run_state.json
  repository_profile.json
  code_evidence.jsonl
  graph_evidence.jsonl
  hypotheses.jsonl
  debate_rounds.jsonl
  findings.json
  events.jsonl
  sessions.json
  tests/
  report.md
```

Write checkpoints to a sibling temporary file, `flush()` and `os.fsync()`, then `os.replace()`. Append events with monotonically increasing sequence numbers. Store model/session/cost metadata but never environment variables, absolute paths, full source files or raw tool arguments containing suspected secrets.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_ledger.py -q`

Expected: append, checkpoint, resume and redaction tests pass.

- [ ] **Step 5: Commit Task 6**

```powershell
git add -- saads_grill_agent/ledger.py tests/saads_grill_agent/test_ledger.py
git commit -m "feat: persist adversarial review ledger"
```

---

### Task 7: Validate and publish autonomous regression-test drafts

**Files:**
- Create: `saads_grill_agent/test_artifacts.py`
- Create: `tests/saads_grill_agent/test_test_artifacts.py`

**Interfaces:**
- Produces: `validate_test_draft(draft, profile) -> ValidatedTestArtifact` and `write_test_artifact()`.
- Consumes: confirmed `Finding`, signed evidence, repository test-framework profile and structured `GeneratedTestDraft`.

- [ ] **Step 1: Write failing safety-policy tests**

```python
@pytest.mark.parametrize("source", [
    "import subprocess\nsubprocess.run(['curl', url])",
    "import requests\nrequests.post('https://target.example')",
    "const cp = require('child_process'); cp.exec('id')",
    "await fetch('https://target.example')",
])
def test_generated_test_rejects_external_or_process_access(source: str) -> None:
    with pytest.raises(TestArtifactPolicyError):
        validate_test_draft(test_draft(source=source), repository_profile())
```

Add passing cases for pytest/FastAPI `TestClient` with dependency overrides and Vitest/Jest tests with mocked `fetch`; add failures for unknown framework, absolute paths, target-repo writes, missing finding/evidence IDs and source over 30 KiB.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_test_artifacts.py -q`

Expected: import fails because `test_artifacts.py` does not exist.

- [ ] **Step 3: Implement structured test drafts and policy**

`GeneratedTestDraft` contains `test_id`, `finding_id`, language (`python/typescript/javascript`), framework (`pytest/vitest/jest`), suggested target-relative path, source, expected failing assertion, mocked dependencies, required fixtures and suggested run command. Python uses `ast.parse()` and rejects imports/calls involving `subprocess`, `socket`, `requests`, `urllib`, `httpx`, `os.system`, `eval` and `exec`. JavaScript/TypeScript rejects `child_process`, `net`, `dgram`, unmocked `fetch`/`axios`, dynamic import and process execution tokens.

Only confirmed findings receive tests. Code-team review verifies that imports, functions and fixtures exist in the repository snapshot. On failure, the test-strategist Agent receives the exact objections and may regenerate twice; after the second failure the artifact status becomes `generation_failed`, while the finding remains confirmed.

- [ ] **Step 4: Write tests outside the target repository**

Write to `<run-dir>/tests/<finding-id>.<py|test.ts|test.js>` and a `test_manifest.json`. The manifest states that tests are unexecuted, includes the snapshot ID, framework, suggested copy destination and suggested run command. The audit system never invokes target test code.

- [ ] **Step 5: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_test_artifacts.py -q`

Expected: safe mocked tests publish; network/process/destructive drafts fail closed.

- [ ] **Step 6: Commit Task 7**

```powershell
git add -- saads_grill_agent/test_artifacts.py tests/saads_grill_agent/test_test_artifacts.py
git commit -m "feat: publish reviewed regression test drafts"
```

---

### Task 8: Render the evidence-backed report

**Files:**
- Create: `saads_grill_agent/report.py`
- Create: `tests/saads_grill_agent/test_report.py`

**Interfaces:**
- Produces: `render_report(state) -> str` and `write_reports(state, run_dir)`.
- Consumes: completed or interrupted `AssessmentState`; performs no model calls.

- [ ] **Step 1: Write a failing report contract test**

```python
def test_report_separates_confirmed_rejected_and_duplicate_items() -> None:
    report = render_report(state_with_all_terminal_states())

    assert "## 已确认漏洞" in report
    assert "## 已驳回假设" in report
    assert "app/rag.py:41" in report
    assert "## 证据与裁决审计" in report
    assert "攻击面覆盖与盲区" not in report
    assert "资源限制" not in report
```

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_report.py -q`

Expected: import fails because `report.py` does not exist.

- [ ] **Step 3: Implement deterministic report sections**

The report contains only: run metadata and target snapshot; executive summary; repository architecture/trust seams; severity counts; confirmed findings; rejected and duplicate hypotheses; generated test manifest; evidence and adjudication audit. Coverage matrices, unreviewed paths, resource limits and separate limitation sections stay out of the user-facing report.

Each confirmed finding includes root cause, plausible attack path, attacker preconditions, impact, whichever code and/or GraphRAG evidence the judge accepted, defender’s strongest rebuttal, why it failed, judge rationale, confidence, remediation and test artifact status. Write a machine-readable `findings.json` from the same models.

Severity is derived locally rather than accepted from model text. Classify impact as `high` for secrets, privileged tool effects, cross-user data or code execution; `medium` for integrity loss, unauthorized model behavior or non-secret disclosure; `low` for bounded quality degradation. Classify exploitability as `high` for default reachable unauthenticated input, `medium` for authenticated/user-assisted input, and `low` for privileged access or non-default configuration. Use this matrix:

```text
                 exploitability
impact           high       medium     low
high             critical   high       medium
medium           high       medium     low
low              medium     low        low
```

Map the judge's confidence score to `high` at `>=0.80`, `medium` at `>=0.55`, and `low` below `0.55`. Confidence does not depend on a fixed number or combination of code and GraphRAG records.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `uv run pytest tests/saads_grill_agent/test_report.py -q`

Expected: section, citation, escaping and status-separation tests pass.

- [ ] **Step 5: Commit Task 8**

```powershell
git add -- saads_grill_agent/report.py tests/saads_grill_agent/test_report.py
git commit -m "feat: render evidence-backed grill reports"
```

---

### Task 9: Add CLI, packaging and target fixture acceptance

**Files:**
- Create: `saads_grill_agent/__main__.py`
- Create: `tests/saads_grill_agent/test_cli.py`
- Create: `tests/fixtures/vulnerable_llm_app/`
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Modify: `README.md`

**Interfaces:**
- Produces: `python -m saads_grill_agent start TARGET_REPO` and `python -m saads_grill_agent resume RUN_DIR`.
- Consumes: an authorized local target path and optional review goal/profile overrides.

- [ ] **Step 1: Write failing CLI tests**

```python
def test_start_prints_run_and_report_paths(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "start", str(fixture_repo()),
            "--authorization-ref", "fixture-test",
            "--output-root", str(tmp_path),
        ],
        run_assessment=fake_completed_assessment,
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "run_state.json" in output
    assert "report.md" in output


def test_start_requires_explicit_local_repository(tmp_path: Path) -> None:
    assert main(["start", "https://example.test/repo.git"]) == 2
```

Add resume, snapshot-mismatch, budget-exceeded and interrupted-report exit cases.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest tests/saads_grill_agent/test_cli.py -q`

Expected: import fails because `__main__.py` does not exist.

- [ ] **Step 3: Implement exact CLI options**

```text
python -m saads_grill_agent start TARGET_REPO
  --authorization-ref TEXT
  [--goal TEXT]
  [--profile profile.yaml]
  [--output-root artifacts/grill_runs]
  [--max-rounds 4]
  [--max-cost-usd 25]

python -m saads_grill_agent resume RUN_DIR
```

`start` requires a nonempty `--authorization-ref`, resolves and validates the target directory, records that reference in run metadata, loads `.env` only from the SAADS project root, loads the existing `SecurityGraph`, and creates a unique run directory. `resume` reloads the exact target path, snapshot and session IDs; mismatches fail closed.

- [ ] **Step 4: Create a deterministic vulnerable fixture**

The fixture includes three known flaws and one defended non-finding:

1. RAG content concatenated with trusted instructions without provenance separation.
2. Model-selected tool name checked after argument execution planning.
3. Debug endpoint returns the assembled system prompt.
4. A high-risk file-write tool protected by a hard allowlist and human-approval branch; this hypothesis must be rejected.

Its tests and manifests identify Python/FastAPI/pytest so generated tests have a stable framework target.

- [ ] **Step 5: Integrate packaging and docs**

Add `saads_grill_agent` to Hatch packages, ignore `artifacts/grill_runs/`, and document the read-only autonomous test-draft safety model. Do not change the existing `saads_attack_agent` command.

- [ ] **Step 6: Run complete offline verification**

```powershell
uv run pytest tests/saads_attack_agent tests/saads_grill_agent -q
uv run python -m saads_grill_agent --help
uv run python -m compileall -q saads_attack_agent saads_grill_agent
```

Expected: all tests pass, both existing and new CLIs import, and compilation exits `0`.

- [ ] **Step 7: Commit Task 9**

```powershell
git add -- saads_grill_agent/__main__.py tests/saads_grill_agent/test_cli.py tests/fixtures/vulnerable_llm_app
git add -p -- pyproject.toml .gitignore README.md
git diff --cached --check
git commit -m "feat: add adversarial repository review CLI"
```

---

### Task 10: Verify the Agent SDK application and run one authorized live assessment

**Files:**
- Create: `reports/grill_agent_sdk_verification.md`
- Runtime output: `artifacts/grill_runs/<run-id>/`

**Interfaces:**
- Consumes: completed implementation, existing GraphRAG index, `.env`, and the local fixture repository.
- Produces: verifier report plus one fully auditable run.

- [ ] **Step 1: Run all offline gates**

```powershell
uv run pytest -q
uv run python -m compileall -q saads_grill_agent
```

Expected: zero failures.

- [ ] **Step 2: Invoke `agent-sdk-verifier-py`**

Verify programmatic subagents, strict MCP config, `dontAsk`, target-instruction isolation, structured outputs, resume handling, tool hooks, cost limits, and absence of write/execute/network tools. Record evidence in `reports/grill_agent_sdk_verification.md`.

- [ ] **Step 3: Run one explicit live fixture assessment**

```powershell
uv run python -m saads_grill_agent start tests/fixtures/vulnerable_llm_app --authorization-ref "fixture-live-acceptance" --goal "审查提示注入、工具调用和敏感信息泄露" --max-cost-usd 25
```

Expected: run completes or produces a resumable interrupted state; it never modifies the fixture.

- [ ] **Step 4: Validate acceptance facts**

The run is accepted only when:

- target fixture hash is unchanged before and after;
- every confirmed finding has at least one accepted signed evidence ID from code, GraphRAG or both, plus a judge confidence score;
- each of the three seeded vulnerabilities reaches an autonomous final `confirmed`, `rejected` or `duplicate` state;
- the defended file-write hypothesis is rejected with its allowlist/approval evidence;
- no hypothesis bypasses the code-team rebuttal and judge stages;
- two empty autonomous discovery sweeps are recorded internally;
- generated tests are outside the fixture and marked unexecuted;
- `report.md`, `findings.json`, debate and audit artifacts agree on IDs and statuses;
- `report.md` contains no coverage, unreviewed-scope, resource-limit or human-validation section.

- [ ] **Step 5: Commit only the verification report**

```powershell
git add -- reports/grill_agent_sdk_verification.md
git commit -m "test: verify adversarial repository grill agent"
```

## Official SDK References

- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [Programmatic subagents](https://code.claude.com/docs/en/agent-sdk/subagents)
- [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)
- [Structured outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs)
- [Sessions and resume](https://code.claude.com/docs/en/agent-sdk/sessions)
- [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)
- [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks)
- [Custom in-process MCP tools](https://code.claude.com/docs/en/agent-sdk/custom-tools)
