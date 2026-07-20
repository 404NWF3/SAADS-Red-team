# GraphRAG 与 SAADS-Red-team 项目技术说明

> 面向大模型应用安全防御的可审计知识图谱检索增强生成工程

**文档版本：** 1.0  
**项目快照：** 2026-07-20  
**代码包名称：** `llm-defense-graphrag` 0.1.0  
**当前索引状态：** Standard 索引已完成；四模式技术冒烟通过；完整人工评测待完成

<!-- PAGEBREAK -->

## 文档目的与阅读指南

本文面向项目维护者、安全研究人员、知识工程人员和评审人员，既解释 Microsoft GraphRAG 的基本思想与工程机制，也逐项说明本仓库如何把它用于大模型应用安全防御知识库。文中严格区分三类内容：

- **GraphRAG 通用机制**：来自 Microsoft 官方文档、项目仓库和研究论文；
- **当前项目事实**：来自本仓库的代码、配置、构建产物与报告；
- **改进建议**：基于现状提出，不代表已经实现。

建议首次阅读依次查看“执行摘要”“GraphRAG 原理”“项目架构”和“当前质量与边界”；运维人员可直接跳到“运行手册”和“故障排查”。

## 目录

1. 执行摘要
2. GraphRAG：概念、索引与检索
3. 项目定位、目标与边界
4. 总体架构与代码组成
5. 语料采集、溯源与完整性
6. GraphRAG 配置与领域建模
7. 索引构建、产物与生命周期
8. 四类查询模式与选型
9. 质量评估、测试与可视化看板
10. 安全、治理与运维控制
11. 已知限制、风险与路线图
12. 操作手册与故障排查
13. 附录：术语、文件索引与参考资料

# 1. 执行摘要

本项目将权威或官方的大模型安全资料转换为带来源元数据的结构化语料，再使用 Microsoft GraphRAG 3.1.1 的 Standard 方法抽取实体、关系与社区，生成可同时支持事实定位、实体邻域分析、全局主题归纳和多跳研究的索引。其核心价值不是“让模型记住更多文本”，而是为回答保留来源、关系方向、社区结构和可重复构建证据。

> **关键结论：** 当前工程链路已经完整贯通，但成熟度应描述为“可审计的研究与内部分析基线”，而不是“已经完成生产验收的安全决策系统”。主要原因是 40 题评测只运行了 4 题冒烟，人工标注仍待完成，图谱还存在少量类型越界、孤立节点和关系方向候选问题。

## 1.1 当前项目快照

| 指标 | 当前值 | 解释 |
|---|---:|---|
| 语料文档 | 297 | 与审计 manifest 行数一致 |
| Text units | 403 | 采用 1200 token 分块、100 token 重叠 |
| 实体 | 2,973 | 主要为攻击技术、组件与防御控制 |
| 关系 | 5,481 | 描述攻击、缓解、实现、评估等有向语义 |
| 社区 / 社区报告 | 636 / 630 | 支持跨文档主题汇总与 Global 检索 |
| 向量表 | 3 | `entity_description`、`community_full_content`、`text_unit_text` |
| 向量维度 | 2,048 | 智谱 `embedding-3` |
| 构建耗时 | 1,824.185 秒 | 约 30 分 24 秒；2026-07-20 的已完成构建 |
| 查询冒烟 | 4/4 成功 | Basic、Local、Global、DRIFT 各 1 题 |
| Python 测试 | 16/16 通过 | 本文生成前在当前工作区复核 |
| 前端测试 | 2/2 通过 | 含前端生产构建与服务端渲染检查 |

## 1.2 项目最有价值的设计

- 语料只来自 MITRE ATLAS、OWASP、Microsoft PyRIT 和 NVIDIA garak 的权威或官方入口，不用搜索结果或模型补写内容凑数。
- 每篇文档记录 canonical URL、版本、许可证、原始快照、检索时间、字数、字节数和 SHA-256，可验证来源与本地转换结果。
- 领域 Prompt 将实体限制为七类，并明确攻击、弱点、组件、控制、工具、标准和评估之间的关系方向。
- 单一构建入口执行语料门禁、模型连通性预检、互斥锁、Standard 索引、Parquet/LanceDB 验收、图谱分析和四模式冒烟。
- 查询评测将问题按 Basic、Local、Global、DRIFT 路由，并要求人工检查证据落地、攻防区分、关系方向和不确定性披露。
- 看板使用静态导出的图谱快照，前端不包含 API 密钥；浏览器内检索不消耗模型 API，再由用户复制 CLI 命令执行真实 GraphRAG 查询。

## 1.3 需要优先处理的事项

1. 统一模型治理：仓库级 `AGENTS.md` 要求使用 GLM 系列模型，而当前 `settings.yaml`、适配器、测试和构建报告使用 DeepSeek completion 加智谱 embedding。两者必须选择其一并形成单一事实来源。
2. 完成 40 题评测与人工标注，不能用 4 题冒烟替代质量结论。
3. 在抽取后增加七类 allowlist 校验或归一化，处理 2 个 `PERSON` 和 1 个 `API` 越界实体。
4. 审核报告中列出的关系方向异常候选，并降低 254 个孤立节点与 259 个未覆盖攻击实体带来的检索盲区。
5. 明确看板定位：当前是静态证据探索器，不是在线 GraphRAG API 服务。

<!-- PAGEBREAK -->

# 2. GraphRAG：概念、索引与检索

## 2.1 从传统 RAG 到 GraphRAG

传统向量 RAG 通常把文档切成文本块，计算向量，在查询时找出与问题最相似的若干文本块，再交给大模型生成回答。它擅长“某个事实在哪里”“某段原文如何描述”之类的局部问题，但面对跨文档关系、多跳依赖和全局主题时容易失效：与问题最相似的少数片段未必代表整个语料，也不显式保存实体之间的结构。

GraphRAG 在向量检索之外增加知识图谱和社区摘要。索引阶段用大模型从文本块中抽取实体与关系，聚合跨文本描述，对图进行社区发现，并为多个层级的社区预生成报告。查询阶段可以根据问题粒度选择文本、实体邻域、社区报告或迭代式多跳探索。

| 维度 | 传统向量 RAG | GraphRAG |
|---|---|---|
| 核心索引 | 文本块及其向量 | 文本块、实体、关系、社区、报告及向量 |
| 擅长问题 | 明确事实、原文定位 | 局部关系、跨文档主题、多跳研究 |
| 全局理解 | 依赖少量相似片段，容易遗漏 | 可对社区报告执行 map-reduce 汇总 |
| 关系表达 | 多为隐式共现 | 显式实体关系与描述 |
| 建索引成本 | 相对低 | Standard 方法需要大量 LLM 抽取与摘要 |
| 审计难点 | 片段来源和生成答案 | 还需审计实体归并、关系方向和社区报告 |

GraphRAG 不是数据库真值系统，也不会自动消除幻觉。它只是把可检索上下文组织得更结构化；最终质量仍由语料、Prompt、抽取模型、归并、社区质量、检索参数和回答约束共同决定。

## 2.2 两阶段生命周期

<!-- FIGURE:architecture -->

**阶段 A：离线索引。** 加载文档并分块；抽取实体、关系和可选 claims；合并实体及关系描述；检测图社区；生成社区报告；为文本块、实体描述和社区内容计算向量；写出 Parquet 与向量库。

**阶段 B：在线或交互式查询。** 根据问题选择检索策略，组装受 token 预算约束的上下文，调用 completion 模型生成带数据引用的回答。索引构建通常远比单次查询昂贵，因此缓存、增量更新和版本管理十分重要。

## 2.3 Standard 索引方法

Microsoft 官方将 Standard 描述为使用 LLM 完成主要推理任务的高保真路径。本项目实际启用的主要步骤是：

1. 读取 `input/_corpus.json`，保留文档 ID、标题、正文和原始元数据。
2. 按 token 分块，并把标题、来源、信任级别、URL、版本等字段前置到每个文本块。
3. 使用领域 Prompt 抽取实体、关系和描述；本项目关闭 claims 抽取。
4. 汇总同一实体及同一关系在多个文本块中的描述。
5. 对图执行社区发现，并按社区生成带数据引用的中文报告。
6. 将文本块、实体描述和社区完整内容写入向量库。
7. 输出 `documents`、`text_units`、`entities`、`relationships`、`communities`、`community_reports` 六类 Parquet 表。

Standard 的优势是实体和关系描述较丰富，适合图谱探索和高保真领域分析；代价是图抽取往往占据主要索引成本。Microsoft 还提供 FastGraphRAG，以 NLP 短语抽取和共现关系降低成本，但图更嘈杂。本项目选择 Standard，符合“安全关系方向和审计细节优先于最低成本”的目标。

## 2.4 GraphRAG 知识模型

| 产物 | 含义 | 本项目用途 |
|---|---|---|
| `documents` | 原始输入文档及元数据 | 追溯来源、标题和文档级范围 |
| `text_units` | 分块后的检索单元 | Basic 检索、Local/DRIFT 的原文证据 |
| `entities` | 归并后的实体与摘要描述 | 定位攻击、控制、组件、工具等对象 |
| `relationships` | 实体间的有向关系及权重 | 分析利用、缓解、实现、评估等路径 |
| `communities` | 图中紧密关联的层次化社区 | 组织跨文档主题与局部子图 |
| `community_reports` | 社区级摘要、发现和评级 | Global 检索及 DRIFT 的广域起点 |
| LanceDB 向量表 | 文本、实体与社区内容的向量 | 相似度召回与上下文定位 |

<!-- PAGEBREAK -->

## 2.5 四类查询模式

| 模式 | 主要上下文 | 适合的问题 | 主要代价或风险 |
|---|---|---|---|
| Basic | 最相似的文本块 | 定义、原文定位、单一来源事实 | 缺少图结构，跨文档综合能力有限 |
| Local | 相关实体、关系、文本块和社区信息 | 具体实体、邻接关系、局部缓解措施 | 高度依赖实体归并和关系方向正确性 |
| Global | 多个社区报告的 map-reduce | 全局主题、共性模式、领域全景 | 资源消耗较高；社区摘要可能压缩细节 |
| DRIFT | 社区起点、实体邻域、文本块及迭代追问 | 多跳路径、跨组件依赖、纵深防御 | 综合推演更强，也更需要逐条来源复核 |

## 2.6 何时值得使用 GraphRAG

当问题主要是精确查找一段事实、语料规模小、实体关系不重要或预算很低时，普通向量 RAG 更简单。以下情形更适合 GraphRAG：

- 同一对象在多个文档中有不同描述，需要归并；
- 问题要求解释“谁影响谁”“哪项控制缓解哪类攻击”；
- 需要从整个语料总结主题、差异或共性；
- 需要跨多个跳点追踪攻击路径、组件依赖和控制链；
- 需要把检索结果映射到社区、实体和原始文本证据。

# 3. 项目定位、目标与边界

## 3.1 项目定位

`SAADS-Red-team` 工作区中的 Python 包名为 `llm-defense-graphrag`。它面向大模型应用安全防御，目标是建立一个可审计、可重复构建、可按关系检索的知识底座，连接权威安全框架、攻击技术、防御控制、系统组件和红队评估工具。

项目不是通用爬虫，也不是自动替代安全专家的决策引擎。采集层拒绝用模型合成内容填补缺失来源；Agent 只编排确定性采集和验证命令；图谱回答在对外发布前仍需要人工审阅。

## 3.2 设计目标

- **可信来源：** 优先权威框架和官方工具文档，来源注册表显式记录许可证与信任级别。
- **可重复：** 固定依赖版本、Prompt、模型配置、语料 manifest 和缓存命名空间。
- **可审计：** 每篇文档可回到 canonical URL、原始快照和 SHA-256；查询答案要求保留 GraphRAG 数据引用。
- **领域化：** 用七类实体和攻防关系方向约束抽取，而不是直接使用通用实体类型。
- **可观测：** 构建摘要、图谱质量报告、查询评测和静态看板形成多个观察面。
- **最小权限：** Claude Agent SDK 只允许读取类工具和三条确定性 Bash 命令。

## 3.3 明确边界

- 当前语料主要覆盖 MITRE ATLAS，来源结构不均衡，不能代表全部 LLM 安全知识。
- `extract_claims.enabled=false`，项目不建立独立的 claims/covariates 事实层。
- 只完成四模式各 1 题冒烟，不等于 40 题评测或持续回归全部通过。
- 静态看板的证据搜索运行在浏览器内，不调用 GraphRAG completion API。
- 项目没有实现对外服务认证、多租户、在线速率限制、审计日志平台或生产 SLA。
- 图谱中的社区和 LLM 生成摘要是检索辅助结构，不应被当作规范性标准原文。

<!-- PAGEBREAK -->

# 4. 总体架构与代码组成

## 4.1 分层架构

<!-- FIGURE:project -->

架构分为六层：来源注册与采集、规范化语料、GraphRAG 索引、查询与评测、质量分析、静态看板。API 密钥只在本地 `.env` 中加载；前端只读取导出的 JSON 快照。

## 4.2 核心组件职责

| 组件 | 主要职责 | 关键输入 / 输出 |
|---|---|---|
| `llm_defense_graphrag/corpus.py` | 下载、转换、校验与写出审计语料 | 来源 YAML → raw、Markdown、manifest、`_corpus.json` |
| `scripts/collect_corpus.py` | 采集器 CLI | `--strict`、`--validate-only`、文档门槛 |
| `settings.yaml` | GraphRAG 模型、分块、存储、工作流和查询配置 | 环境变量、Prompt、LanceDB |
| `deepseek_completion.py` | 适配 DeepSeek 的结构化输出模式 | Pydantic schema → `json_object`，本地仍校验 |
| `scripts/graphrag_cli.py` | 注册适配器后转交官方 CLI | `index`、`query`、`prompt-tune` 等 |
| `scripts/build_graphrag.py` | 单入口构建与验收 | 预检、锁、Standard index、分析、冒烟 |
| `scripts/analyze_graph.py` | 图谱质量分析 | Parquet → JSON/Markdown 质量报告 |
| `scripts/evaluate_queries.py` | 四模式评测 | 问题集 → JSONL 回答与 summary |
| `scripts/export_dashboard_data.py` | 导出前端静态快照 | Parquet + reports → `graphrag.json` |
| `dashboard/app/page.tsx` | 态势、图谱、查询和质量界面 | 静态快照 → 浏览器交互 |
| `llm_defense_graphrag/agent.py` | Claude Agent SDK 采集编排 | 项目 Skill 与确定性命令 allowlist |

## 4.3 目录地图

```text
SAADS-Red-team/
├─ config/corpus_sources.yaml       # 来源注册表
├─ data/raw/                        # 原始下载快照（运行后生成）
├─ input/                           # 逐篇 Markdown 与 _corpus.json
├─ prompts/                         # 正式启用的领域 Prompt
├─ prompts/tuned/                   # prompt-tune 原始产物，供审计
├─ output/                          # 六类 Parquet 与 LanceDB
├─ reports/                         # 语料、构建、图谱质量、查询评测报告
├─ eval/questions.yaml              # 40 道中文问题与人工检查项
├─ llm_defense_graphrag/            # Python 包、采集器和模型适配器
├─ scripts/                         # 构建、分析、查询、导出与可视化脚本
├─ dashboard/                       # Next.js/Vinext 静态态势看板
├─ tests/                           # Python 单元测试
├─ settings.yaml                    # GraphRAG 主配置
└─ main.py                          # 可选 Claude Agent SDK 入口
```

## 4.4 数据流与控制流

1. `corpus_sources.yaml` 声明来源类型、URL、许可证、信任级别和筛选规则。
2. 采集器写出原始快照和带 YAML front matter 的逐篇 Markdown，同时生成 manifest 与 `_corpus.json`。
3. 构建器校验至少 100 篇、manifest 与 JSON 数量一致，并对 completion/embedding 各执行一次连通性预检。
4. 互斥锁防止两个索引进程同时写同一个 `output/`。
5. GraphRAG Standard 生成 Parquet、社区报告和 LanceDB。
6. 构建器验证六类 Parquet 非空与向量库存在，随后运行图谱质量分析和四模式冒烟。
7. 导出脚本把质量、语料、评测与图谱压缩为前端快照；看板只读该快照。

# 5. 语料采集、溯源与完整性

## 5.1 当前来源构成

<!-- FIGURE:sources -->

| 来源 | 文档数 | 占比 | 信任级别 | 主要价值 |
|---|---:|---:|---|---|
| MITRE ATLAS | 271 | 91.25% | authoritative | 攻击技术、缓解、案例与显式关系 |
| NVIDIA garak | 15 | 5.05% | official_project | LLM 漏洞探测、探针与评估 |
| OWASP LLM Top 10 2025 | 10 | 3.37% | authoritative | LLM 应用风险与缓解叙述 |
| Microsoft PyRIT | 1 | 0.34% | official_project | 生成式 AI 红队方法与工具 |

来源比例显示出明显的 ATLAS 主导结构。这有利于攻击技术覆盖，却可能让工具使用、应用架构控制和治理实践在图中的权重偏低。NIST 被记录为下一批候选，但当前项目坚持只在获得稳定的 NIST 自有全文入口后加入，不用镜像替代。

## 5.2 三类采集适配器

**ATLAS YAML。** 下载官方最新 YAML，保留原文件；按 technique、mitigation 和 case-study 等对象拆分文档；写入结构化字段和显式 ATLAS relationships；canonical URL 指向 ATLAS 对应对象页面。

**HTML 页面。** 针对 OWASP 官方风险页，移除脚本、样式、导航、页眉页脚和表单，提取正文标题、段落、列表和预格式化文本；页面正文少于 100 词即失败。

**GitHub 文档快照。** 下载指定分支 ZIP，记录归档 SHA-256、ETag 和 Last-Modified；按 include 规则筛选 Markdown/RST；用安全关键词评分选出限定数量的文档；canonical URL 指向官方仓库文件。

## 5.3 文档审计字段

manifest 为每篇文档保存以下字段：

- 标识与路径：`id`、`path`、`raw_path`；
- 来源与语义：`title`、`source`、`source_type`、`security_domain`、`trust_level`；
- 时间与版本：`published_at`、`document_version`、`retrieved_at`；
- 法务与溯源：`canonical_url`、`license`；
- 完整性：`word_count`、`byte_count`、`sha256`。

离线验证会检查文档数门槛、manifest 与 `_corpus.json` 数量一致、ID 与路径不重复、必填字段不为空、canonical URL 使用 HTTPS、本地规范化文件与 raw 快照均存在，以及 Markdown 文件 SHA-256 与 manifest 一致。

## 5.4 采集可靠性设计

- 下载客户端跟随重定向，超时 40 秒，失败最多重试 3 次并采用 1、2 秒退避。
- 各来源隔离失败；非严格模式可保留已成功来源并记录错误，严格模式在写出报告后失败。
- 新一轮采集会删除旧 manifest 中、但本轮已不再生成的 Markdown 文件，避免陈旧文档继续进入索引。
- 每次采集按来源与 ID 排序，生成稳定的输出顺序。
- 采集器不会调用 LLM 来生成或替代原始资料。

# 6. GraphRAG 配置与领域建模

## 6.1 当前模型配置

| 任务 | 当前实现 | 配置要点 |
|---|---|---|
| Completion | DeepSeek `deepseek-v4-flash` | OpenAI-compatible；显式关闭 thinking；每 10 秒最多 20 请求 |
| Embedding | 智谱 `embedding-3` | OpenAI-compatible；2,048 维；每 10 秒最多 5 请求 |
| 可选 Agent 编排 | Claude Agent SDK 0.2.122 | 只用于采集工作流，不参与 GraphRAG 抽取或查询 |

所有密钥从 `.env` 注入，文档只列变量名：`DEEPSEEK_API_KEY`、`DEEPSEEK_API_BASE`、`DEEPSEEK_CHAT_MODEL`、`ZHIPU_API_KEY`、`ZHIPU_API_BASE`、`ZHIPU_EMBEDDING_MODEL`、`ZHIPU_EMBEDDING_DIMENSIONS`。可选 Agent 另需 `ANTHROPIC_API_KEY` 或有效 Claude Code 登录。

> **治理提醒：** `AGENTS.md` 当前要求“使用 glm 系列的模型”，但实际 GraphRAG 完成模型为 DeepSeek。这不是运行时错误，却是文档、配置和团队规则之间的冲突。下一次索引前应明确采用 GLM completion 还是继续 DeepSeek，并同步 `settings.yaml`、适配器、测试、README、缓存目录和构建预检。

## 6.2 DeepSeek 结构化输出适配

GraphRAG 会把 Pydantic 模型类作为结构化 `response_format`。当前适配器把这种请求转换为 DeepSeek 支持的 `{"type":"json_object"}`，但不移除 GraphRAG 的本地 Pydantic 校验。这样既满足 API 兼容性，又保留返回结构验证。适配器以单例 provider 注册，项目 CLI 在加载官方 GraphRAG 命令前完成注册。

## 6.3 分块与元数据前置

- 分块类型：token；
- 最大块大小：1,200 token；
- 重叠：100 token；
- 编码模型：`cl100k_base`；
- 前置字段：title、source、source_type、published_at、security_domain、trust_level、canonical_url、document_version。

元数据前置让实体抽取与回答更容易知道证据来自哪里，但也会占用每个块的 token 预算。当前 297 篇文档生成 403 个 text units，平均约 1.36 个 text units/文档；对于大量短 ATLAS 条目，这种分布是可以解释的，但仍应通过更完整的检索评测确认分块是否最优。

## 6.4 七类领域实体

<!-- FIGURE:entities -->

| 实体类型 | 当前数量 | 语义 |
|---|---:|---|
| `ATTACK_TECHNIQUE` | 987 | 操纵、绕过、污染、泄露、窃取或滥用系统的具体攻击方法 |
| `COMPONENT` | 949 | 模型、检索器、向量库、系统提示、工具执行器等系统边界 |
| `DEFENSE_CONTROL` | 502 | 预防、检测、限制、响应或恢复攻击的具体控制 |
| `VULNERABILITY` | 292 | 使攻击成为可能的设计弱点、暴露或失效条件 |
| `TOOL` | 114 | 可执行或部署的具名红队、测试或防御软件 |
| `EVALUATION` | 75 | 具名基准、测试套件、评估方法或任务 |
| `STANDARD` | 51 | 标准、框架、分类法、控制目录或权威指南 |

Prompt 明确禁止 `PERSON`、`ORGANIZATION`、`API` 等其他类型，但当前图中仍出现 `PERSON` 2 个和 `API` 1 个。这表明 Prompt 约束不是强类型边界，后处理仍需要 allowlist 校验或归一化。

## 6.5 关系方向与证据约束

领域 Prompt 明确推荐以下方向：

- 攻击技术 → 组件：攻击针对组件；
- 攻击技术 → 弱点：攻击利用弱点；
- 防御控制 → 攻击技术 / 弱点：控制缓解攻击或弱点；
- 工具 → 防御控制 / 评估：工具实施控制或执行评估；
- 标准 → 防御控制 / 攻击技术：标准推荐控制或收录攻击；
- 评估 → 组件 / 攻击技术 / 防御控制：评估检验相应对象。

只有文本明确支持时才抽取关系，禁止仅按同段共现建边。关系强度为 1-10：9-10 表示原文直接且核心，6-8 表示关系清晰，1-5 只允许较弱但仍有文本依据的关系。

## 6.6 社区、报告与 claims

社区最大规模配置为 10。社区报告使用中文安全分析 Prompt，要求区分攻防方向、只陈述输入支持的事实、用 GraphRAG 的 `[Data: ...]` 形式引用记录，并把 rating 解释为“对理解或实施 LLM 防御的重要性”，而不是漏洞严重度。

本项目将 claims 抽取关闭。因此任何查询 Prompt 中出现的通用 Claims 示例都不代表实际索引包含 claims 数据；回答不得假设 claims 存在。

## 6.7 缓存、重试与存储

- Completion 与 embedding 均使用指数退避，最多 8 次，基础延时 2 秒、最大 60 秒并带 jitter。
- JSON 缓存目录固定为 `cache/deepseek-v4-flash/`，避免 GraphRAG 3.1.1 的缓存键未包含模型名时误复用旧 GLM 响应。
- 文件输入、输出和日志分别位于 `input/`、`output/` 和 `logs/`。
- LanceDB 位于 `output/lancedb`，向量维度必须与 embedding 返回长度一致。

<!-- PAGEBREAK -->

# 7. 索引构建、产物与生命周期

## 7.1 推荐构建入口

```powershell
uv sync --dev
uv run python scripts/collect_corpus.py --min-docs 100 --strict
uv run python scripts/collect_corpus.py --validate-only --min-docs 100
uv run python scripts/build_graphrag.py --preflight-only
uv run python scripts/build_graphrag.py
```

不建议直接并行启动多个 `graphrag index`。构建器使用 `logs/graphrag-build.lock` 记录 PID 与开始时间，以互斥方式保护同一 `output/`。如果进程异常退出后锁未清理，应先核实记录的进程确实不存在，再人工处理锁文件。

## 7.2 预检门禁

构建器在真正索引前执行：

1. `.env` 存在且七个 GraphRAG 必需变量非空；
2. `_corpus.json` 与 manifest 存在、均不少于 100 条且数量一致；
3. 向 completion 端点发送一条非思考模式连通请求；
4. 向 embedding 端点发送一条连通请求，并确认向量长度为 2,048。

真正调用 GraphRAG index 时使用 `--skip-validation`，因为构建器已经用同一配置完成显式预检，避免官方 CLI 再消耗重复连通请求。

## 7.3 构建产物验收

`validate_index` 要求六类 Parquet 全部存在且非空，并要求 `output/lancedb/` 存在且包含文件。任何缺失或空表都会使构建失败，防止拿残缺索引执行查询和质量报告。

| 验收对象 | 当前结果 |
|---|---:|
| `documents.parquet` | 297 行 |
| `text_units.parquet` | 403 行 |
| `entities.parquet` | 2,973 行 |
| `relationships.parquet` | 5,481 行 |
| `communities.parquet` | 636 行 |
| `community_reports.parquet` | 630 行 |
| `output/lancedb/` | 已填充三张 2,048 维向量表 |

## 7.4 构建状态记录

`reports/build_summary.json` 记录状态、开始/结束时间、根目录、语料数量、模型、向量维度、各产物行数和总耗时。余额不足等可操作失败会给出中文诊断；智谱 HTTP 429 / code `1113` 会被解释为余额不足或无可用资源包。

当前完成构建开始于 `2026-07-20T08:15:22Z`，结束于 `2026-07-20T08:45:46Z`，状态为 `complete`。该报告是当前索引规模和模型组合的权威本地快照。

## 7.5 何时需要重新构建

- 语料内容、来源版本或转换逻辑变化；
- 实体类型、关系规则或抽取 Prompt 变化；
- completion/embedding 模型、维度或关键参数变化；
- GraphRAG 跨 minor/major 版本升级导致配置或输出结构变化；
- 修复实体归并、关系方向或社区参数后需要重算图谱。

若只更新静态看板数据而索引未变化，可运行导出脚本并重建前端，无需重新调用 LLM。

# 8. 四类查询模式与选型

## 8.1 CLI 入口

所有真实查询都应通过注册兼容 provider 的项目 CLI 执行：

```powershell
uv run python scripts/graphrag_cli.py query --method basic "OWASP 如何描述 Prompt Injection？"
uv run python scripts/graphrag_cli.py query --method local "哪些控制缓解 Prompt Injection？"
uv run python scripts/graphrag_cli.py query --method global "当前语料中的防御体系有哪些主要层次？"
uv run python scripts/graphrag_cli.py query --method drift "RAG 投毒如何跨组件影响高权限工具调用？"
```

评测脚本统一指定 `Multiple Paragraphs with source citations`，以便回答保留数据引用。查询时仍必须检查引用记录是否真正支持紧邻的结论。

## 8.2 模式选择决策

1. 问题能否由一两个原文片段直接回答？能则优先 Basic。
2. 问题是否围绕明确实体、相邻关系或局部控制？是则使用 Local。
3. 问题是否要求覆盖整个语料、比较多个社区或总结共性？是则使用 Global。
4. 问题是否要求从广域主题出发，继续追踪多跳路径并形成纵深方案？是则使用 DRIFT。

当答案用于规范、审计报告或高风险决策时，应同时保留原始来源核验步骤。尤其是 DRIFT，它适合形成研究草案，但更可能混入“基于证据的合理推演”，不能把每句话都视为来源直接陈述。

## 8.3 项目评测集

`eval/questions.yaml` 共 40 道中文题，每种模式 10 道：

- Basic：OWASP 风险定义、ATLAS 技术描述、PyRIT/garak 定位；
- Local：具体攻击、弱点、组件、控制和工具之间的局部关系；
- Global：防御层次、来源差异、共同原则和图谱枢纽；
- DRIFT：跨组件攻击链、纵深防御、持续验证和跨边界信任链。

每条结果预留四个人工检查项：答案是否由索引来源支撑、攻防是否混淆、关系方向是否正确、是否披露不确定性或证据缺口。

# 9. 质量评估、测试与可视化看板

## 9.1 图谱质量现状

| 指标 | 当前值 | 解读 |
|---|---:|---|
| 越界实体 | 3 / 2,973 | 约 0.10%；类型强校验待补 |
| 孤立节点 | 254 | 占 8.54%；Local/DRIFT 无法沿关系扩展这些节点 |
| 节点度中位数 / P95 / 最大值 | 2 / 13 / 530 | 图整体偏稀疏，存在一个或少数超高连接枢纽 |
| 攻击—防御两跳覆盖 | 728 / 987 | 73.76%；仍有 259 个攻击实体在两跳内无防御控制 |
| 关系方向异常候选 | 50 条样本 | 报告脚本最多保留 50 条，需人工复核而非直接判错 |
| 社区报告缺标题 / 缺正文 | 0 / 0 | 当前 630 份报告结构完整 |

关系语义统计采用描述关键词多标签命中，因此各语义计数之和可以超过总关系数。当前主要命中包括 `mitigates` 935、`exploits` 784、`targets` 706、`implements` 694、`detects` 325、`evaluates` 215、`recommends` 46，另有 2,538 条归为 `other`。`other` 并不等于错误，只表示未命中当前有限词表。

## 9.2 查询冒烟现状

Basic、Local、Global、DRIFT 各运行 1 题，四条命令均返回成功且有索引引用。人工审阅认为 Basic、Local 和 Global 在来源落地、攻防区分、方向与边界方面通过；DRIFT 的多跳方案完整，但少量工程建议属于证据基础上的推演，发布前需要逐条来源复核。

> **不要误读：** `4/4 passed` 只代表四条冒烟命令与样例输出可用。`questions_defined=40`、`questions_run=4`、`manual_review_pending=true` 才是完整状态。

## 9.3 自动化测试复核

本文生成前在当前工作区执行：

```powershell
uv run pytest -q
# 16 passed

cd dashboard
npm test
# production build succeeded; 2 tests passed
```

Python 测试覆盖配置固定、Prompt 区分、DeepSeek 结构化输出适配、语料转换、评测集数量、图谱方向辅助函数、构建门禁、互斥锁、余额错误和 UTF-8 子进程环境。前端测试验证服务端能渲染看板外壳，并检查静态快照包含完整节点与关系规模。

## 9.4 看板功能与安全边界

看板分为四个主区：

- **态势总览：** 产物规模、攻击—防御两跳覆盖、实体类型、关系语义和高价值社区；
- **图谱探索：** 搜索实体、按类型/关系筛选、查看一跳邻居和实体检查器；
- **查询实验室：** 浏览器内执行无 API 成本的静态证据排序，并生成真实 GraphRAG CLI 命令；
- **质量中心：** 展示来源、孤立率、覆盖率、越界实体、重复候选和冒烟成功率。

Docker 配置只监听 `127.0.0.1:3080`，根文件系统只读，容器使用非 root 用户。前端快照不包含 API 密钥。需要注意，静态证据排序是前端字符串/别名匹配和邻接探索，不等价于 GraphRAG 的 completion 推理。

# 10. 安全、治理与运维控制

## 10.1 密钥与供应商控制

- `.env` 必须保持本地并被 Git 忽略；禁止把真实密钥写入文档、日志、前端快照或问题集。
- 预检会产生真实 API 调用和费用；批量索引前应确认余额、配额和速率限制。
- 模型切换时必须更换缓存命名空间，防止复用旧供应商响应。
- embedding 维度变化时必须同步 `vector_size` 并重建向量库，不能混用旧向量。

## 10.2 不可信语料与 Prompt Injection

GraphRAG 处理的安全文档本身可能包含攻击字符串、提示注入样例和代码。应将所有语料视为数据而不是指令。当前抽取 Prompt 已限定任务和输出格式，但仍建议在后续版本中：

- 在采集与抽取边界显式标记不可信内容；
- 对结构化输出执行 schema/allowlist 强校验；
- 不允许语料改变系统 Prompt、工具权限或模型供应商参数；
- 对包含工具调用建议的查询回答设置人工审批；
- 对外发布前回到 canonical source 核验规范性结论。

## 10.3 Agent 最小权限

Claude Agent SDK 入口只预批准 Read、Glob、Grep；Bash 必须精确匹配三条命令：严格采集、离线验证和 GraphRAG dry-run。其他工具或命令被拒绝。Agent 的预算上限为 2 美元、默认最多 12 turns。采集逻辑仍由确定性 Python 代码执行，Agent 不生成替代语料。

## 10.4 可复现与版本控制

- Python 版本要求为 3.12，依赖由 `uv.lock` 固定；GraphRAG 为 3.1.1。
- Prompt 原始调优产物保存在 `prompts/tuned/`，正式 Prompt 在 `prompts/`，便于比较人工校准。
- 每次重要重建应归档 `build_summary.json`、语料 manifest、质量报告、查询评测和配置指纹。
- GraphRAG minor/major 升级可能改变配置和产物；升级前备份 Prompt 与配置，并按官方迁移说明评估是否需要重建。

# 11. 已知限制、风险与路线图

## 11.1 当前已知限制

- **来源偏斜：** 91.25% 文档来自 MITRE ATLAS；来源数量不等于知识覆盖均衡。
- **评测不足：** 仅运行 4/40，全部人工检查仍未形成结构化标注结果。
- **模式越界：** Prompt 禁止的 `PERSON` 与 `API` 仍进入图谱。
- **关系审计：** 方向异常候选和大量 `other` 关系尚未完成系统性抽样。
- **覆盖缺口：** 26.24% 的攻击实体在两跳内没有防御控制。
- **静态看板：** 没有在线 GraphRAG API、用户身份、查询配额或实时索引刷新。
- **模型治理冲突：** 团队指令要求 GLM，而当前实现固定 DeepSeek completion。
- **无 claims 层：** 无法按独立 claim 生命周期进行事实冲突和时效管理。

## 11.2 建议路线图

| 优先级 | 建议 | 完成标准 |
|---|---|---|
| P0 | 解决 GLM/DeepSeek 治理冲突 | 配置、适配器、测试、文档、缓存与构建报告一致 |
| P0 | 完成 40 题评测 | 40/40 有运行结果，四项人工检查均填值，并形成模式级统计 |
| P0 | 增加实体类型后校验 | 七类之外实体为 0，或全部有显式归一化记录 |
| P0 | 复核关系方向候选 | 候选逐条分类为真错/误报，并回写修复策略 |
| P1 | 降低攻击—防御覆盖缺口 | 建立未覆盖清单，补充权威来源或修正抽取，跟踪覆盖率变化 |
| P1 | 引入质量回归阈值 | 构建在越界率、孤立率、覆盖率或评测退化时失败 |
| P1 | 扩展权威来源 | 仅通过稳定官方入口加入 NIST 等来源，并保持相同审计字段 |
| P1 | 增加成本与缓存观测 | 每阶段记录请求数、token、费用、命中率与失败重试 |
| P2 | 建立 Baseline 对照 | 用同一问题集比较 Basic RAG、Local、Global、DRIFT 的质量与成本 |
| P2 | 生产化查询服务 | 认证、授权、速率限制、审计日志、异步任务、超时和数据版本标识 |

路线图应按“先校准证据和评测，再扩展功能”的顺序执行。当前最重要的不是增加更多界面，而是让模型、Prompt、图谱质量和查询证据形成可重复的验收闭环。

# 12. 操作手册与故障排查

## 12.1 初始化

```powershell
uv sync --dev
Copy-Item .env.example .env  # 仅当本地尚无 .env
```

填写 `.env` 后先运行 `--preflight-only`。不要在聊天、工单或截图中粘贴实际密钥。

## 12.2 采集与离线验证

```powershell
uv run python scripts/collect_corpus.py --min-docs 100 --strict
uv run python scripts/collect_corpus.py --validate-only --min-docs 100
```

严格模式要求所有配置来源成功。离线验证不访问网络，适合 CI 或重建前快速检查。

## 12.3 构建与查询

```powershell
uv run python scripts/build_graphrag.py --preflight-only
uv run python scripts/build_graphrag.py

uv run python scripts/graphrag_cli.py query --method local "哪些防御控制可以缓解 Prompt Injection？"
```

## 12.4 评测与质量报告

```powershell
uv run python scripts/analyze_graph.py
uv run python scripts/evaluate_queries.py --smoke
uv run python scripts/evaluate_queries.py
```

完整评测会覆盖 40 题并消耗更多 API 资源。建议在结果 JSONL 上完成独立人工标注，不要只阅读 summary。

## 12.5 看板

```powershell
uv run python scripts/export_dashboard_data.py
docker compose -f dashboard/compose.yaml up -d --build
# 浏览器访问 http://127.0.0.1:3080
```

Node.js 开发模式：

```powershell
cd dashboard
npm ci
npm run dev
npm test
```

## 12.6 常见故障

| 现象 | 可能原因 | 处理方法 |
|---|---|---|
| 缺少环境变量 | `.env` 不存在或变量为空 | 从 `.env.example` 创建并只在本地填写 |
| embedding 返回 429 / 1113 | 余额不足或无可用资源包 | 充值或配置资源包后重跑；缓存会复用已成功响应 |
| embedding 维度不一致 | 模型返回维度与 2,048 配置不同 | 同步环境变量、`vector_size`，清理不兼容向量库并重建 |
| 存在 build lock | 另一个构建在运行，或异常退出遗留锁 | 核实 PID；仅在确认无活动构建后移除锁 |
| 六类 Parquet 缺失或为空 | 索引中断或输出不完整 | 不要查询；修复上游错误后重新构建 |
| Windows 输出编码失败 | 子进程继承 GBK，源文本含特殊字符 | 项目构建器已强制 `PYTHONUTF8=1` 和 UTF-8 I/O；优先用构建器 |
| 查询无引用或答非所问 | 路由不合适、Prompt/索引质量不足 | 切换模式，检查原始 context，并回到来源验证 |
| 看板数据陈旧 | 索引/报告更新后未重新导出 | 运行 `export_dashboard_data.py` 并重建镜像 |
| Agent 启动失败 | 无 `ANTHROPIC_API_KEY` 或有效登录 | 配置凭据；不影响直接运行确定性采集与 GraphRAG |

# 13. 附录

## 13.1 术语表

| 术语 | 说明 |
|---|---|
| RAG | Retrieval-Augmented Generation，先检索外部知识再生成回答 |
| GraphRAG | 将实体关系图、社区和社区报告纳入索引与检索的 RAG 方法 |
| Text unit | 文档切分后的检索与抽取单元 |
| Entity | 从文本抽取并跨文本归并的对象 |
| Relationship | 两个实体之间带方向、描述和权重的连接 |
| Community | 图中相互关联较紧密的层次化实体群组 |
| Community report | 由社区实体与关系生成的主题报告 |
| Local Search | 围绕具体实体与邻域组装上下文的查询方式 |
| Global Search | 对社区报告执行 map-reduce 的全局查询方式 |
| DRIFT | 结合社区起点、局部邻域与迭代追问的检索方式 |
| LanceDB | 本项目保存文本、实体和社区向量的本地向量库 |
| Grounding | 让回答中的判断能回到索引记录和原始来源 |
| Manifest | 记录每篇规范化文档来源、版本、路径和完整性摘要的清单 |

## 13.2 项目事实来源索引

| 主题 | 仓库文件 |
|---|---|
| 项目说明与命令 | `README.md` |
| 依赖与版本 | `pyproject.toml`、`uv.lock` |
| GraphRAG 配置 | `settings.yaml` |
| 来源注册表 | `config/corpus_sources.yaml` |
| 语料采集与审计 | `llm_defense_graphrag/corpus.py` |
| 构建与预检 | `scripts/build_graphrag.py` |
| 模型适配器 | `llm_defense_graphrag/deepseek_completion.py` |
| 图谱质量算法 | `scripts/analyze_graph.py` |
| 评测集与执行器 | `eval/questions.yaml`、`scripts/evaluate_queries.py` |
| 当前构建事实 | `reports/build_summary.json` |
| 当前质量事实 | `reports/graph_quality.json`、`reports/graph_quality.md` |
| 查询冒烟结论 | `reports/query_smoke_review.md` |
| 看板 | `dashboard/README.md`、`dashboard/app/page.tsx` |

## 13.3 官方参考资料

1. Microsoft GraphRAG - Indexing Architecture：[官方架构文档](https://microsoft.github.io/graphrag/index/architecture/)
2. Microsoft GraphRAG - Indexing Methods：[官方索引方法](https://microsoft.github.io/graphrag/index/methods/)
3. Microsoft GraphRAG - Query Engine Overview：[官方查询概览](https://microsoft.github.io/graphrag/query/overview/)
4. Microsoft GraphRAG - Outputs：[官方产物说明](https://microsoft.github.io/graphrag/index/outputs/)
5. Microsoft GraphRAG - Detailed Configuration：[官方配置参考](https://microsoft.github.io/graphrag/config/yaml/)
6. Microsoft GraphRAG GitHub Repository：[官方代码仓库](https://github.com/microsoft/graphrag)
7. Edge 等，GraphRAG 研究论文《From Local to Global》：[论文页面](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/)

## 13.4 文档状态声明

本文依据 2026-07-20 当前工作区、现有索引与报告编制。测试复核未发起新的 completion 或 embedding API 调用；模型可用性和余额以最近一次构建报告为准。凡涉及安全规范、产品决策或对外结论，仍应核对 canonical source，并对 GraphRAG 引用进行逐条人工验证。
