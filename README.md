# llm-defense-graphrag

面向大模型应用安全防御的可审计 GraphRAG 工程。本阶段固定 Python 3.12、`uv`、Microsoft GraphRAG 3.1.1、DeepSeek V4 Flash 文本生成、智谱 embedding-3 向量化，以及可重复的官方语料采集/转换流程。

当前 Standard 索引已构建完成：297 篇文档、403 个 text units、2973 个实体、5481 条关系、636 个社区和 630 份社区报告。LanceDB 包含 `entity_description`、`community_full_content`、`text_unit_text` 三张 2048 维向量表；Basic、Local、Global、DRIFT 四模式冒烟均通过。详细结果见 `reports/build_summary.json`、`reports/graph_quality.md` 和 `reports/query_smoke_review.md`。

## 为什么选择这些来源

| 来源 | 用途 | 获取方式 | 信任级别 |
|---|---|---|---|
| [MITRE ATLAS](https://github.com/mitre-atlas/atlas-data) | 攻击战术、技术、缓解、案例与显式关系；首批规模主源 | 官方月度 YAML | authoritative |
| [OWASP LLM Top 10 2025](https://genai.owasp.org/llm-top-10/) | LLM 应用风险与缓解叙述 | 10 个官方风险页面 | authoritative |
| [Microsoft PyRIT](https://github.com/Azure/PyRIT) | 生成式 AI 红队方法与工具 | 官方仓库文档快照 | official_project |
| [NVIDIA garak](https://github.com/NVIDIA/garak) | LLM 漏洞探测与评估 | 官方仓库文档快照 | official_project |

不靠批量抓取搜索结果或模型补写内容凑数。每篇文档保留 canonical URL、版本、许可、原始快照路径、字数与 SHA-256。

NIST 仍列为下一批优先候选，但只有在验证出当前可达、NIST 自有且稳定的全文入口后才会加入；不会用镜像替代官方来源。

## 初始化与配置

```powershell
uv sync --dev
Copy-Item .env.example .env  # 仅在本地尚无 .env 时执行
```

`.env` 中 GraphRAG 必需变量为：

```dotenv
DEEPSEEK_API_KEY=...
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-v4-flash

ZHIPU_API_KEY=...
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_EMBEDDING_MODEL=embedding-3
ZHIPU_EMBEDDING_DIMENSIONS=2048
```

`settings.yaml` 通过 OpenAI-compatible provider 调用两个服务。DeepSeek `deepseek-v4-flash` 负责实体/关系抽取、摘要、社区报告和 Basic/Local/Global/DRIFT 查询回答，并显式关闭默认思考模式；智谱 `embedding-3` 只负责 2048 维向量化，LanceDB 的 `vector_size` 同步固定为 2048。completion 限制为每 10 秒最多 20 个请求，并使用独立的 `cache/deepseek-v4-flash/` 缓存命名空间，防止模型切换后误用旧 GLM 响应。项目 CLI 适配层把 GraphRAG 的 Pydantic `json_schema` 请求转换成 DeepSeek 支持的 `json_object` API 模式，返回后仍由 GraphRAG 执行原始 Pydantic 校验。Claude Agent SDK 只编排本地采集工作流，不作为 GraphRAG 的推理/嵌入模型；运行 Agent 入口时另需 `ANTHROPIC_API_KEY` 或有效的 Claude Code 登录。

## 采集与验证

```powershell
uv run python scripts/collect_corpus.py --min-docs 100 --strict
uv run python scripts/collect_corpus.py --validate-only --min-docs 100
uv run python scripts/graphrag_cli.py index --dry-run
```

`scripts/graphrag_cli.py index --dry-run` 会各发送一条 completion 与 embedding 请求来验证模型配置，因此也需要有效余额。

输出：

- `data/raw/<source>/`：下载的原始 YAML、HTML、仓库 ZIP 与元数据；
- `input/{mitre,owasp,nist,tools}/`：逐篇 Markdown，带固定元数据头；
- `input/_corpus.json`：GraphRAG 实际读取的结构化语料，配合 `chunking.prepend_metadata`；
- `reports/corpus_manifest.csv`：逐篇审计 manifest；
- `reports/corpus_summary.json`：来源分布与失败信息。

## 领域 Prompt 与 Standard 索引

`prompts/tuned/` 保留 GraphRAG `prompt-tune` 的原始产物供审计；正式启用的是 `prompts/` 根目录下人工校准的 UTF-8 Prompt。实体抽取严格限制为：

- `ATTACK_TECHNIQUE`
- `DEFENSE_CONTROL`
- `COMPONENT`
- `VULNERABILITY`
- `TOOL`
- `STANDARD`
- `EVALUATION`

`extract_claims.enabled` 保持为 `false`。推荐使用单一构建入口。它先验证 100 篇门槛、DeepSeek completion 与智谱 embedding 资源，持有单实例锁，然后依次执行 Standard 索引、六类 Parquet/LanceDB 验收、图谱分析与四模式冒烟：

```powershell
uv run python scripts/build_graphrag.py --preflight-only
uv run python scripts/build_graphrag.py
```

构建状态写入 `reports/build_summary.json`。构建器在索引阶段使用 `--skip-validation`，因为它已用同一配置完成显式模型预检，避免 GraphRAG 再消耗两次重复连通请求。

不要同时启动多个 `graphrag index` 进程写同一个 `output/`。索引成功后应存在 `documents`、`text_units`、`entities`、`relationships`、`communities`、`community_reports` 六个 Parquet 文件，以及 `output/lancedb/` 向量库。

DeepSeek completion 与智谱 embedding 都必须有有效密钥和余额。如果智谱返回 HTTP 429 / code `1113`（余额不足或无可用资源包），先充值或配置可用资源包，再重跑同一索引命令；GraphRAG 会复用 `cache/` 中已成功且与当前模型配置匹配的响应。不要用残缺的 `output/` 执行查询或质量验收。

## 查询评测与质量报告

`eval/questions.yaml` 定义 40 道中文题，Basic、Local、Global、DRIFT 各 10 道。冒烟模式每种路由运行第一题；完整评测不带 `--smoke`：

```powershell
uv run python scripts/evaluate_queries.py --smoke
uv run python scripts/evaluate_queries.py
```

结果写入 `reports/query_evaluation.jsonl` 和对应 summary；每条记录保留回答、耗时、返回码与待人工标注项。`scripts/analyze_graph.py` 输出 `reports/graph_quality.json` 与 `reports/graph_quality.md`，涵盖实体类型、重复候选、关系语义/方向、度分布、孤立节点、社区摘要和攻击—防御两跳覆盖。

## Claude Agent SDK workflow

项目 Skill 位于 `.claude/skills/collect-defense-corpus/`。SDK 入口显式使用 `setting_sources=["project"]` 与 `skills=["collect-defense-corpus"]`：

```powershell
uv run python main.py
```

采集器是确定性执行面；Agent 负责按 Skill 运行、审计和解释失败，不生成替代语料。
