# GraphRAG 图谱质量报告

## 产物规模

- documents: 297
- text_units: 403
- entities: 2973
- relationships: 5481
- communities: 636
- community_reports: 630

## 实体类型

- ATTACK_TECHNIQUE: 987
- COMPONENT: 949
- DEFENSE_CONTROL: 502
- VULNERABILITY: 292
- TOOL: 114
- EVALUATION: 75
- STANDARD: 51
- PERSON: 2
- API: 1
- 越界类型: API, PERSON

## 关系与连通性

- 关系语义分布: {"other": 2538, "mitigates": 935, "exploits": 784, "targets": 706, "implements": 694, "detects": 325, "evaluates": 215, "recommends": 46}
- 方向异常候选: 50
- 孤立节点: 254 (8.54%)
- 节点度：min=0, median=2.0, p95=13.0, max=530
- 攻击—防御两跳覆盖: 728/987 (73.76%)

## 社区报告

- 报告数: 630
- 缺少标题: 0
- 缺少正文: 0

详细候选与样本见 `reports/graph_quality.json`。
