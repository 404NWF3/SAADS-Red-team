# Summary-only GraphRAG

本项目使用 Microsoft GraphRAG 3.1.1、GLM `glm-4.5-air` 和智谱
`embedding-3`，从 `data/items_20260713T095333Z.csv` 的 `summary` 列构建
面向大模型应用安全的知识图谱。

## 数据边界

构建入口只读取 CSV 的 `summary` 列。每行被转换为仅包含
`id`、`title`、`text` 的中间文档，其中 `id` 和 `title` 是按行号生成的
无语义标识，`text` 是去除首尾空白后的原始 `summary`。CSV 的其他列不会
进入输入文档、Prompt、实体属性或查询上下文。

全量构建会逐行比较：

1. CSV `summary`；
2. `summary_input/summary_corpus.json` 中的 `text`；
3. `output/documents.parquet` 中的 `text` 和 `raw_data`。

任一行不一致都会令构建失败。

## 三层实体对齐

实体抽取后、社区发现和向量化前执行统一对齐：

1. **抽取约束**：`prompts/extract_graph.txt` 要求使用规范名称，避免产生新的
   拼写变体。
2. **确定性注册表**：`config/entity_aliases.yaml` 处理已知缩写、空格、连字符
   和历史名称；注册表带版本号，可审计、可回滚。
3. **GLM 消歧**：对归一化后仍有歧义的候选使用同一 GLM 模型判定规范名称和
   类型；只接受候选集合内的名称、允许的类型以及不低于 `0.90` 的置信度。

随后会重新聚合重复实体和关系、重写关系端点、删除合并产生的自环，并生成
`output/entity_alignment.parquet` 审计表。当前规范结果包括：

| 输入变体 | 规范实体 |
|---|---|
| `AIBOM` / `AI BOM` | `AIBOM` |
| `HUGGINGFACE` / `HUGGING FACE` | `HUGGING FACE` |
| `FINE-TUNING` / `FINETUNING` | `FINE TUNING PIPELINE` |
| `LLM` / `LARGE LANGUAGE MODEL (LLM)` | `LLM` |

## 配置

```powershell
uv sync --dev
Copy-Item .env.example .env
```

`.env` 至少需要：

```dotenv
ZAI_API_KEY=...
ZAI_CHAT_MODEL=glm-4.5-air
ZHIPU_API_KEY=...
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_EMBEDDING_MODEL=embedding-3
ZHIPU_EMBEDDING_DIMENSIONS=2048
```

GLM 使用 OpenAI-compatible API。项目适配器将 GraphRAG 的 Pydantic
`json_schema` 请求转换为 `json_object`，响应仍由本地 Pydantic 校验；结构错误
会收到一次明确的纠正提示并重试。

## 构建

先做 API 与配置预检：

```powershell
uv run python scripts/build_graphrag.py --preflight-only
```

从 CSV 重新生成输入并全新构建：

```powershell
uv run python scripts/build_graphrag.py --fresh
```

`--fresh` 是必需的：已有 `output/` 会先归档到 `backups/`，避免旧索引污染。
不要并发启动多个索引进程写入同一个 `output/`。

也可单独生成 summary-only 中间语料：

```powershell
uv run python scripts/prepare_summary_corpus.py
```

## 当前全量产物

2026-07-27 的全量构建结果：

| 产物 | 行数 |
|---|---:|
| 文档 / text units | 6,843 / 6,843 |
| 实体 | 10,408 |
| 关系 | 11,329 |
| 社区 | 1,809 |
| 社区报告 | 1,808 |
| 实体对齐审计记录 | 11,734 |

对齐修改了 969 条抽取实体；低于置信度门槛的记录为 0，关系自环为 0，关系端点
缺失为 0。三个 LanceDB 表分别包含 10,408、1,808、6,843 条 2048 维向量。
Basic、Local、Global、DRIFT 四种查询冒烟测试均通过。

社区 `469` 的报告因 GLM 服务端内容过滤（错误码 `1301`）无法生成，因此社区报告
比社区数少 1；图、文本单元、实体、关系和其他社区报告均完整。

主要产物：

- `reports/build_summary.json`：构建、模型和 summary 来源核验摘要；
- `reports/entity_alignment.json`：实体对齐审计报告；
- `reports/graph_quality.json`：图结构质量分析；
- `reports/query_evaluation.jsonl`：查询评测结果；
- `output/*.parquet`：GraphRAG 表；
- `output/lancedb/`：向量索引。

## 测试与查询

```powershell
uv run pytest -q
uv run python scripts/evaluate_queries.py --smoke
uv run python scripts/graphrag_cli.py query --root . --method local "你的问题"
```

## 对抗性仓库审查（saads_grill_agent）

`saads_grill_agent` 对**明确授权的本地** LLM 应用仓库做只读、多智能体代码审计。目标仓库始终视为不可信数据：不加载其 `.claude` / Skills / MCP / hooks 作为指令，也不连接目标模型、部署环境或外部网络。

安全模型要点：

- 需要非空 `--authorization-ref` 才可启动；拒绝 URL / 远程仓库路径。
- 红队与代码团队只能通过只读 MCP 工具引用已签发证据；只有独立裁判可确认或驳回假设。
- 生成的回归测试草稿只写入评估产物目录（默认 `artifacts/grill_runs/`），**不写入目标仓库、不自动执行**，并禁止网络、系统命令、凭据读取和破坏性文件操作。
- `.env` 仅从本 SAADS 项目根加载；复用现有 GraphRAG 与 DeepSeek Agent SDK 约定。
- 不改变现有 `python -m saads_attack_agent` 命令。

```powershell
uv run python -m saads_grill_agent start TARGET_REPO --authorization-ref "ticket-or-approval-id"
uv run python -m saads_grill_agent resume RUN_DIR
```

可选参数：`--goal`、`--profile profile.yaml`、`--output-root artifacts/grill_runs`、`--max-rounds 4`、`--max-cost-usd 25`。
