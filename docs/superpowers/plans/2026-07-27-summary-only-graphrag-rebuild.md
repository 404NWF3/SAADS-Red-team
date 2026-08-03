# Summary-Only GraphRAG Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fresh GraphRAG index from all 6,843 non-empty `summary` values in `data/items_20260713T095333Z.csv`, without adding any other CSV field to GraphRAG input, while enforcing prompt-, rule-, and GLM-based entity alignment.

**Architecture:** A dedicated corpus converter emits an isolated JSON corpus whose document text is exactly the trimmed `summary` value and whose IDs/titles are synthetic row ordinals. A project-owned GraphRAG workflow wraps the stock `extract_graph` workflow and aligns entity and relationship tables before finalization, communities, reports, and embeddings. Deterministic aliases resolve known variants; unresolved lexical/type conflicts are adjudicated through the configured GLM completion model and recorded in an audit table.

**Tech Stack:** Python 3.12, pytest, pandas, PyYAML, Microsoft GraphRAG 3.1.1, GraphRAG completion API, GLM completion, Zhipu embedding-3, Parquet, LanceDB.

## Global Constraints

- Only `data/items_20260713T095333Z.csv` is an input source.
- Only the CSV `summary` field may become GraphRAG document text; all other CSV field values are forbidden from the generated corpus.
- Structural `id` and `title` values must be synthetic and derived only from the row ordinal.
- GraphRAG extraction must receive summary text without prepended metadata.
- Do not patch files under `.venv`; register project-owned workflows through GraphRAG's workflow factory.
- Use a GLM-series completion model from `.env` through the standard GraphRAG completion API.
- Preserve all pre-existing unrelated worktree changes and do not stage or commit them.
- The final index must be rebuilt from an empty `output/` with a fresh model cache namespace.

---

### Task 1: Summary-Only Corpus Boundary

**Files:**
- Create: `llm_defense_graphrag/summary_corpus.py`
- Create: `scripts/prepare_summary_corpus.py`
- Create: `tests/test_summary_corpus.py`
- Modify: `settings.yaml`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: UTF-8-SIG CSV path and output JSON path.
- Produces: `prepare_summary_corpus(csv_path: Path, output_path: Path) -> SummaryCorpusStats`.
- Produces corpus rows shaped exactly as `{"id": "summary-000001", "title": "Summary 000001", "text": "<trimmed summary>"}`.

- [ ] **Step 1: Write the failing summary-isolation test**

```python
def test_prepare_summary_corpus_uses_only_summary_values(tmp_path: Path) -> None:
    source = tmp_path / "items.csv"
    source.write_text(
        "item_id,title,summary,source_uri\n"
        "forbidden-id,forbidden-title,Allowed summary.,https://forbidden.test\n",
        encoding="utf-8-sig",
    )

    output = tmp_path / "summary_corpus.json"
    stats = prepare_summary_corpus(source, output)
    rows = json.loads(output.read_text(encoding="utf-8"))

    assert rows == [{
        "id": "summary-000001",
        "title": "Summary 000001",
        "text": "Allowed summary.",
    }]
    assert stats.total_rows == 1
    assert stats.written_rows == 1
    assert "forbidden" not in output.read_text(encoding="utf-8").lower()
```

- [ ] **Step 2: Run the test and verify it fails because the module is missing**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_summary_corpus.py -v`

Expected: FAIL during import of `llm_defense_graphrag.summary_corpus`.

- [ ] **Step 3: Implement strict CSV conversion**

Implement:

```python
@dataclass(frozen=True)
class SummaryCorpusStats:
    total_rows: int
    written_rows: int
    empty_rows: int


def prepare_summary_corpus(csv_path: Path, output_path: Path) -> SummaryCorpusStats:
    ...
```

The function must require a `summary` header, reject empty summaries, trim only surrounding whitespace, emit only the three allowed JSON keys, and write UTF-8 JSON atomically.

- [ ] **Step 4: Add missing-column and empty-summary tests**

The tests must assert that either condition raises `SummaryCorpusError` with the row number where applicable.

- [ ] **Step 5: Configure an isolated GraphRAG input**

Set:

```yaml
input:
  type: json
  file_pattern: "^summary_corpus\\.json$"
  encoding: utf-8
  id_column: id
  title_column: title
  text_column: text
  prepend_metadata: []

input_storage:
  type: file
  base_dir: "summary_input"
```

Add `summary_input/` to `.gitignore`; the preparation CLI writes `summary_input/summary_corpus.json`.

- [ ] **Step 6: Run the focused tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_summary_corpus.py tests/test_settings.py -v`

Expected: PASS.

---

### Task 2: Deterministic Entity Alignment

**Files:**
- Create: `config/entity_aliases.yaml`
- Create: `llm_defense_graphrag/entity_alignment.py`
- Create: `tests/test_entity_alignment.py`

**Interfaces:**
- Consumes: extracted entity and relationship DataFrames.
- Produces: `align_graph_tables(entities, relationships, registry, resolver) -> AlignmentResult`.
- `AlignmentResult` contains aligned entities, aligned relationships, and an audit DataFrame.

- [ ] **Step 1: Write failing tests for the four observed variant groups**

Literal expectations:

```python
assert canonical("AI BOM", "DEFENSE_CONTROL") == ("AIBOM", "DEFENSE_CONTROL")
assert canonical("AIBOM", "COMPONENT") == ("AIBOM", "DEFENSE_CONTROL")
assert canonical("HUGGINGFACE", "COMPONENT") == ("HUGGING FACE", "COMPONENT")
assert canonical("LARGE LANGUAGE MODEL (LLM)", "COMPONENT") == ("LLM", "COMPONENT")
assert canonical("FINE-TUNING", "COMPONENT") == (
    "FINE TUNING PIPELINE", "COMPONENT"
)
assert canonical("FINETUNING", "ATTACK_TECHNIQUE") == (
    "MALICIOUS FINE TUNING", "ATTACK_TECHNIQUE"
)
```

- [ ] **Step 2: Run tests and verify missing implementation failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_entity_alignment.py -v`

Expected: FAIL importing the alignment module.

- [ ] **Step 3: Implement registry loading and deterministic normalization**

Implement NFKC normalization, uppercase/collapsed whitespace, exact typed aliases, untyped aliases, acronym expansion, and lexical signatures. Registry aliases must take precedence over heuristics.

- [ ] **Step 4: Write failing graph-remap test**

The fixture must contain duplicate alias nodes and relationships. Assert that alignment:

- unions descriptions and text-unit IDs;
- sums frequencies and relationship weights;
- rewrites both relationship endpoints;
- removes self-loops created only by alias collapse;
- leaves no relationship endpoint absent from the aligned entity titles;
- produces one audit row per original entity.

- [ ] **Step 5: Implement DataFrame alignment**

Group aligned entities by `(canonical_title, canonical_type)`, remap relationships, aggregate duplicate edges, and reject a raw title that resolves to more than one canonical target because GraphRAG relationships do not carry endpoint types.

- [ ] **Step 6: Run focused tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_entity_alignment.py -v`

Expected: PASS.

---

### Task 3: GLM Ambiguity Resolver and GraphRAG Workflow

**Files:**
- Create: `llm_defense_graphrag/graphrag_workflows.py`
- Modify: `scripts/graphrag_cli.py`
- Modify: `settings.yaml`
- Modify: `.env.example`
- Modify: `tests/test_settings.py`
- Extend: `tests/test_entity_alignment.py`

**Interfaces:**
- Consumes: GraphRAG `LLMCompletion` created from `default_completion_model`.
- Produces: `GlmAmbiguityResolver.resolve(candidates) -> list[AlignmentDecision]`.
- Produces: `run_extract_graph_with_alignment(config, context) -> WorkflowFunctionOutput`.

- [ ] **Step 1: Write a failing resolver-contract test**

Use a small async fake only at the external completion boundary. Return a complete GraphRAG-style response containing validated JSON and assert parsing of:

```json
{
  "decisions": [
    {
      "source_title": "EXAMPLE-NAME",
      "source_type": "COMPONENT",
      "canonical_title": "EXAMPLE NAME",
      "canonical_type": "COMPONENT",
      "same_entity": true,
      "confidence": 0.96,
      "reason": "Equivalent spelling"
    }
  ]
}
```

Malformed JSON, missing candidates, invalid entity types, and confidence below `0.90` must not auto-merge.

- [ ] **Step 2: Verify the resolver tests fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_entity_alignment.py -v`

Expected: FAIL because `GlmAmbiguityResolver` is missing.

- [ ] **Step 3: Implement the resolver through GraphRAG completion**

Use `graphrag_llm.completion.create_completion`, the workflow cache child `entity_alignment`, temperature zero, a JSON-only prompt, and local validation. Only unresolved lexical/acronym candidate groups may call the resolver.

- [ ] **Step 4: Switch completion configuration to GLM**

Use:

```yaml
completion_models:
  default_completion_model:
    model_provider: openai
    model: ${ZAI_CHAT_MODEL}
    auth_method: api_key
    api_key: ${ZAI_API_KEY}
    api_base: ${ZHIPU_API_BASE}
```

Keep Zhipu `embedding-3`; change cache base directory to a fresh GLM summary-only namespace.

- [ ] **Step 5: Wrap and register the stock workflow**

The wrapper must:

1. await the stock `extract_graph` workflow;
2. read `entities` and `relationships`;
3. align both tables;
4. overwrite both tables before `finalize_graph`;
5. write `entity_alignment` as an audit Parquet table.

Register the wrapper in `scripts/graphrag_cli.py` without modifying GraphRAG package files.

- [ ] **Step 6: Run focused and settings tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_entity_alignment.py tests/test_settings.py -v`

Expected: PASS.

---

### Task 4: Fresh Build Orchestration and Quality Gates

**Files:**
- Modify: `scripts/build_graphrag.py`
- Modify: `tests/test_build_graphrag.py`
- Modify: `scripts/analyze_graph.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: source CSV and generated summary corpus.
- Produces: a fresh `output/`, `reports/build_summary.json`, `reports/entity_alignment.json`, and updated graph-quality report.

- [ ] **Step 1: Write failing build-boundary tests**

Tests must prove:

- `validate_corpus` reads `summary_input/summary_corpus.json`;
- corpus rows contain exactly `id`, `title`, `text`;
- document text equals the expected summary fixture;
- GLM completion preflight uses `ZAI_API_KEY`, `ZHIPU_API_BASE`, and `ZAI_CHAT_MODEL`;
- the build summary records source CSV, summary row count, GLM model, and embedding model;
- index validation requires the alignment audit artifact.

- [ ] **Step 2: Verify the tests fail against the current DeepSeek/old-corpus build**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_build_graphrag.py -v`

Expected: FAIL on the old corpus path and DeepSeek request.

- [ ] **Step 3: Implement preparation, GLM preflight, and fresh-output handling**

The build entry point must prepare the summary corpus before model calls, validate all 6,843 rows, and require an explicitly fresh output directory. Existing `output/` must be moved to a timestamped backup before indexing rather than merged or reused.

- [ ] **Step 4: Add entity-alignment quality gates**

Require:

- no forbidden aliases `AI BOM`, `HUGGINGFACE`, `LARGE LANGUAGE MODEL (LLM)`, `FINE-TUNING`, or `FINETUNING`;
- canonical titles are unique;
- relationship endpoints are a subset of entity titles;
- no self-loop introduced by alignment;
- audit table contains all input-to-canonical decisions;
- GraphRAG required Parquet files and LanceDB tables are non-empty.

- [ ] **Step 5: Run the complete unit suite**

Run: `.\.venv\Scripts\python.exe -m pytest -q`

Expected: all tests pass.

---

### Task 5: Full Summary-Only GraphRAG Rebuild

**Files/Artifacts:**
- Source: `data/items_20260713T095333Z.csv`
- Generated: `summary_input/summary_corpus.json`
- Generated: `output/*.parquet`
- Generated: `output/lancedb/`
- Generated: `reports/build_summary.json`
- Generated: `reports/entity_alignment.json`
- Generated: `reports/graph_quality.json`

**Interfaces:**
- Consumes: completed implementation and valid `.env`.
- Produces: the final clean GraphRAG index.

- [ ] **Step 1: Discover and configure an available GLM chat model**

Use the configured Z.AI endpoint and key without printing secrets. Record only the selected model name. Add `ZAI_CHAT_MODEL` to `.env` if it is absent.

- [ ] **Step 2: Prepare and independently verify the corpus**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_summary_corpus.py
```

Verify:

- exactly 6,843 documents;
- zero empty summaries;
- every generated row has exactly `id`, `title`, and `text`;
- every generated `text` equals the corresponding trimmed CSV `summary`;
- no generated `text` contains a value copied from another CSV field by the converter.

- [ ] **Step 3: Run model preflight**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\build_graphrag.py --preflight-only
```

Expected: GLM completion and Zhipu embedding checks pass.

- [ ] **Step 4: Rebuild from scratch**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\build_graphrag.py --fresh
```

Continue monitoring until Standard indexing, alignment, finalization, communities, reports, embeddings, analysis, and smoke queries finish successfully.

- [ ] **Step 5: Perform the completion audit**

Re-run the full test suite and independently inspect corpus counts, GraphRAG row counts, alias absence, endpoint integrity, alignment audit coverage, LanceDB tables and dimensions, build status, and smoke-query status. Completion requires evidence for every global constraint, not only a zero exit code.

