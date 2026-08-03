# GraphRAG 图谱质量报告

## 产物规模

- documents: 6843
- text_units: 6843
- entities: 10408
- relationships: 11329
- communities: 1809
- community_reports: 1808

## 实体类型

- COMPONENT: 4665
- VULNERABILITY: 2344
- ATTACK_TECHNIQUE: 1225
- DEFENSE_CONTROL: 1217
- EVALUATION: 530
- TOOL: 332
- STANDARD: 87
- LLM: 5
- SYSTEM: 1
- ORGANIZATION: 1
- 容易被忽略的依赖项: 1
- 越界类型: LLM, ORGANIZATION, SYSTEM, 容易被忽略的依赖项

## 关系与连通性

- 关系语义分布: {"other": 5833, "targets": 1837, "exploits": 1402, "evaluates": 868, "implements": 796, "mitigates": 785, "detects": 529, "recommends": 79}
- 方向异常候选: 38
- 孤立节点: 781 (7.50%)
- 节点度：min=0, median=1.0, p95=5.0, max=1412
- 攻击—防御两跳覆盖: 733/1225 (59.84%)

## 社区报告

- 报告数: 1808
- 缺少标题: 0
- 缺少正文: 0

详细候选与样本见 `reports/graph_quality.json`。
