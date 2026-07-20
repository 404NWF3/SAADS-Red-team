from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


RELATION_TERMS = {
    "mitigates": ("mitigat", "prevent", "protect", "缓解", "防止", "保护"),
    "exploits": ("exploit", "利用"),
    "targets": ("target", "针对"),
    "detects": ("detect", "monitor", "检测", "监测"),
    "evaluates": ("evaluat", "assess", "test", "评估", "测试"),
    "implements": ("implement", "enforce", "实施", "执行"),
    "recommends": ("recommend", "require", "建议", "要求"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the GraphRAG inline visualization.")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def primary_semantic(description: object) -> str:
    lowered = str(description).lower()
    for label, terms in RELATION_TERMS.items():
        if any(term in lowered for term in terms):
            return label
    return "other"


def safe_json(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def load_data(root: Path) -> dict[str, object]:
    output = root / "output"
    reports = root / "reports"
    entities = pd.read_parquet(output / "entities.parquet")
    relationships = pd.read_parquet(output / "relationships.parquet")
    community_reports = pd.read_parquet(output / "community_reports.parquet")
    quality = json.loads((reports / "graph_quality.json").read_text(encoding="utf-8"))
    corpus = json.loads((reports / "corpus_summary.json").read_text(encoding="utf-8"))
    build = json.loads((reports / "build_summary.json").read_text(encoding="utf-8"))

    nodes: list[list[object]] = []
    node_index: dict[str, int] = {}
    for row in entities[["title", "type", "degree"]].itertuples(index=False):
        title = str(row.title)
        node_index[title] = len(nodes)
        nodes.append([title, str(row.type), int(row.degree)])

    edges: list[list[object]] = []
    for row in relationships[["source", "target", "description", "weight"]].itertuples(index=False):
        source = node_index.get(str(row.source))
        target = node_index.get(str(row.target))
        if source is None or target is None:
            continue
        edges.append(
            [source, target, primary_semantic(row.description), round(float(row.weight), 2)]
        )

    community_points: list[list[object]] = []
    for row in community_reports[["community", "rank", "size", "level", "title"]].itertuples(index=False):
        rank = 0.0 if pd.isna(row.rank) else round(float(row.rank), 1)
        size = 0 if pd.isna(row.size) else int(row.size)
        level = 0 if pd.isna(row.level) else int(row.level)
        community_points.append([int(row.community), rank, size, level, str(row.title)])

    top_communities = [
        [int(row.community), round(float(row.rank), 1), int(row.size), str(row.title)]
        for row in community_reports.sort_values(
            ["rank", "size"], ascending=[False, False]
        )[["community", "rank", "size", "title"]]
        .head(10)
        .itertuples(index=False)
    ]

    artifacts = quality["artifacts"]
    vector_records = (
        artifacts["entities"] + artifacts["community_reports"] + artifacts["text_units"]
    )
    coverage = quality["attack_defense_path_coverage"]
    degree = quality["degree"]
    return {
        "snapshot": build["finished_at"],
        "artifacts": artifacts,
        "vectorRecords": vector_records,
        "models": build["models"],
        "elapsedSeconds": build["elapsed_seconds"],
        "entityTypes": quality["entity_types"]["counts"],
        "unknownTypes": quality["entity_types"]["unknown"],
        "relationshipSemantics": quality["relationship_semantics"],
        "sources": corpus["sources"],
        "sourceTypes": corpus["source_types"],
        "securityDomains": corpus["security_domains"],
        "quality": {
            "attackCount": coverage["attack_count"],
            "coveredCount": coverage["covered_count"],
            "coverageRatio": coverage["coverage_ratio"],
            "uncoveredCount": coverage["attack_count"] - coverage["covered_count"],
            "isolatedCount": degree["isolated_count"],
            "isolatedRatio": degree["isolated_ratio"],
            "degreeMinimum": degree["minimum"],
            "degreeMedian": degree["median"],
            "degreeP95": degree["p95"],
            "degreeMaximum": degree["maximum"],
            "duplicateCandidates": len(quality["duplicate_or_synonym_candidates"]),
            "offSchemaEntities": sum(
                int(quality["entity_types"]["counts"].get(kind, 0))
                for kind in quality["entity_types"]["unknown"]
            ),
            "completeReports": artifacts["community_reports"]
            - quality["communities"]["missing_title_count"]
            - quality["communities"]["missing_content_count"],
        },
        "nodes": nodes,
        "edges": edges,
        "communityPoints": community_points,
        "topCommunities": top_communities,
    }


FRAGMENT = r'''<div id="graphrag-atlas" class="graphrag-atlas">
  <style>
    #graphrag-atlas {
      color: var(--foreground);
      background: transparent;
      width: 100%;
      font-family: var(--font-sans, ui-sans-serif, system-ui, sans-serif);
      line-height: 1.4;
    }
    #graphrag-atlas * { box-sizing: border-box; }
    #graphrag-atlas .atlas-stack { display: grid; gap: 14px; }
    #graphrag-atlas .atlas-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    #graphrag-atlas .atlas-card { min-width: 0; }
    #graphrag-atlas .section-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 12px; }
    #graphrag-atlas h2, #graphrag-atlas h3 { margin: 0; color: var(--foreground); }
    #graphrag-atlas h2 { font-size: 1rem; }
    #graphrag-atlas h3 { font-size: .9rem; }
    #graphrag-atlas .subtle, #graphrag-atlas .axis-label { color: var(--muted-foreground); font-size: .76rem; }
    #graphrag-atlas .meta-strip { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; }
    #graphrag-atlas .pipeline { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; }
    #graphrag-atlas .stage { min-width: 0; padding: 10px 8px; border-inline-start: 3px solid var(--viz-series-1); background: color-mix(in srgb, var(--card) 88%, var(--viz-series-1) 12%); }
    #graphrag-atlas .stage:nth-child(2) { border-color: var(--viz-series-2); }
    #graphrag-atlas .stage:nth-child(3) { border-color: var(--viz-series-3); }
    #graphrag-atlas .stage:nth-child(4) { border-color: var(--viz-series-4); }
    #graphrag-atlas .stage:nth-child(5) { border-color: var(--viz-series-5); }
    #graphrag-atlas .stage:nth-child(6) { border-color: var(--viz-series-6); }
    #graphrag-atlas .stage strong { display: block; font-size: 1.15rem; font-variant-numeric: tabular-nums; white-space: nowrap; }
    #graphrag-atlas .stage span { display: block; color: var(--muted-foreground); font-size: .72rem; overflow-wrap: anywhere; }
    #graphrag-atlas .bar-list { display: grid; gap: 7px; }
    #graphrag-atlas .bar-row { display: grid; grid-template-columns: minmax(110px, 1.3fr) minmax(120px, 2fr) 56px; gap: 8px; align-items: center; font-size: .74rem; }
    #graphrag-atlas .bar-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    #graphrag-atlas .bar-track { height: 8px; background: var(--muted); position: relative; }
    #graphrag-atlas .bar-fill { display: block; height: 100%; min-width: 1px; background: var(--bar-color, var(--viz-series-1)); }
    #graphrag-atlas .bar-value { text-align: end; font-variant-numeric: tabular-nums; color: var(--muted-foreground); }
    #graphrag-atlas .quality-list { display: grid; gap: 13px; }
    #graphrag-atlas .quality-row { display: grid; grid-template-columns: minmax(130px, 1fr) minmax(130px, 2fr) 72px; gap: 10px; align-items: center; }
    #graphrag-atlas .quality-row strong { font-size: .78rem; }
    #graphrag-atlas .quality-value { text-align: end; font-size: .78rem; font-variant-numeric: tabular-nums; }
    #graphrag-atlas .progress { height: 12px; background: var(--muted); position: relative; overflow: hidden; }
    #graphrag-atlas .progress > span { display: block; height: 100%; background: var(--viz-series-3); }
    #graphrag-atlas .metric-line { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
    #graphrag-atlas .metric-line div { border-top: 1px solid var(--border); padding-top: 7px; }
    #graphrag-atlas .metric-line strong { display: block; font-size: .95rem; font-variant-numeric: tabular-nums; }
    #graphrag-atlas .metric-line span { display: block; color: var(--muted-foreground); font-size: .7rem; }
    #graphrag-atlas .gap-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
    #graphrag-atlas .gap-cell { padding: 8px; border-inline-start: 3px solid var(--viz-series-2); background: color-mix(in srgb, var(--card) 90%, var(--viz-series-2) 10%); }
    #graphrag-atlas .gap-cell:nth-child(2) { border-color: var(--viz-series-4); }
    #graphrag-atlas .gap-cell:nth-child(3) { border-color: var(--viz-series-6); }
    #graphrag-atlas .gap-cell:nth-child(4) { border-color: var(--foreground); }
    #graphrag-atlas .gap-cell strong { display: block; font-size: 1rem; font-variant-numeric: tabular-nums; }
    #graphrag-atlas .gap-cell span { display: block; color: var(--muted-foreground); font-size: .7rem; }
    #graphrag-atlas .controls { display: grid; grid-template-columns: minmax(180px, 2fr) minmax(145px, 1fr) minmax(145px, 1fr); gap: 10px; align-items: end; }
    #graphrag-atlas .control { display: grid; gap: 4px; min-width: 0; }
    #graphrag-atlas .control label { color: var(--muted-foreground); font-size: .72rem; }
    #graphrag-atlas .search-wrap { position: relative; }
    #graphrag-atlas .search-results { position: absolute; inset-inline: 0; top: calc(100% + 4px); z-index: 3; display: grid; background: var(--popover, var(--card)); border: 1px solid var(--border); box-shadow: var(--shadow-md); }
    #graphrag-atlas .search-results:empty { display: none; }
    #graphrag-atlas .search-result { appearance: none; border: 0; border-bottom: 1px solid var(--border); background: transparent; color: var(--foreground); text-align: start; padding: 7px 9px; cursor: pointer; font: inherit; font-size: .76rem; }
    #graphrag-atlas .search-result:last-child { border-bottom: 0; }
    #graphrag-atlas .search-result:hover, #graphrag-atlas .search-result:focus-visible { background: var(--accent); color: var(--accent-foreground); outline: none; }
    #graphrag-atlas .network-wrap { margin-top: 10px; border-top: 1px solid var(--border); }
    #graphrag-atlas .network-svg, #graphrag-atlas .scatter-svg { display: block; width: 100%; height: auto; }
    #graphrag-atlas .edge { stroke-width: 1.35; opacity: .6; }
    #graphrag-atlas .node { cursor: pointer; outline: none; }
    #graphrag-atlas .node circle { stroke: var(--background); stroke-width: 2; }
    #graphrag-atlas .node:focus-visible circle { stroke: var(--foreground); stroke-width: 3; }
    #graphrag-atlas .node text { fill: var(--foreground); font-size: 10px; paint-order: stroke; stroke: var(--background); stroke-width: 3px; stroke-linejoin: round; }
    #graphrag-atlas .node.center text { font-size: 12px; font-weight: 650; }
    #graphrag-atlas .legend { display: flex; flex-wrap: wrap; gap: 6px 12px; margin-top: 6px; }
    #graphrag-atlas .legend-item { display: inline-flex; gap: 5px; align-items: center; font-size: .68rem; color: var(--muted-foreground); }
    #graphrag-atlas .legend-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--legend-color); }
    #graphrag-atlas .selection { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; border-top: 1px solid var(--border); padding-top: 10px; }
    #graphrag-atlas .selection strong { display: block; overflow-wrap: anywhere; }
    #graphrag-atlas .selection-detail { color: var(--muted-foreground); font-size: .75rem; margin-top: 2px; }
    #graphrag-atlas .mode-list { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }
    #graphrag-atlas .mode { border-top: 3px solid var(--viz-series-3); padding-top: 7px; }
    #graphrag-atlas .mode strong { display: block; font-size: .78rem; }
    #graphrag-atlas .mode span { color: var(--muted-foreground); font-size: .68rem; }
    #graphrag-atlas .model-grid { display: grid; gap: 8px; margin-top: 12px; }
    #graphrag-atlas .model-row { display: grid; grid-template-columns: 110px minmax(0, 1fr); gap: 8px; font-size: .76rem; }
    #graphrag-atlas .model-row span:first-child { color: var(--muted-foreground); }
    #graphrag-atlas .community-layout { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(250px, .75fr); gap: 14px; }
    #graphrag-atlas .community-list { display: grid; gap: 6px; align-content: start; }
    #graphrag-atlas .community-item { display: grid; grid-template-columns: 42px 38px minmax(0, 1fr); gap: 7px; align-items: baseline; font-size: .72rem; }
    #graphrag-atlas .community-id, #graphrag-atlas .community-rank { color: var(--muted-foreground); font-variant-numeric: tabular-nums; }
    #graphrag-atlas .community-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    #graphrag-atlas .axis { stroke: var(--border); stroke-width: 1; }
    #graphrag-atlas .tick { fill: var(--muted-foreground); font-size: 10px; }
    #graphrag-atlas .point { fill: var(--muted-foreground); opacity: .32; }
    #graphrag-atlas .point.top { fill: var(--viz-series-2); opacity: .85; }
    #graphrag-atlas .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
    @media (max-width: 736px) {
      #graphrag-atlas .atlas-grid, #graphrag-atlas .community-layout { grid-template-columns: 1fr; }
      #graphrag-atlas .pipeline { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      #graphrag-atlas .controls { grid-template-columns: 1fr 1fr; }
      #graphrag-atlas .search-wrap { grid-column: 1 / -1; }
      #graphrag-atlas .gap-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 420px) {
      #graphrag-atlas .pipeline { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      #graphrag-atlas .bar-row { grid-template-columns: minmax(92px, 1fr) minmax(86px, 1.2fr) 48px; gap: 5px; }
      #graphrag-atlas .quality-row { grid-template-columns: 1fr 58px; }
      #graphrag-atlas .quality-row .progress { grid-column: 1 / -1; grid-row: 2; }
      #graphrag-atlas .metric-line { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      #graphrag-atlas .controls { grid-template-columns: 1fr; }
      #graphrag-atlas .search-wrap { grid-column: auto; }
      #graphrag-atlas .selection { grid-template-columns: 1fr; }
      #graphrag-atlas .mode-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>

  <div class="atlas-stack">
    <div class="meta-strip subtle" aria-label="构建元数据">
      <span id="snapshot-label"></span>
      <span id="elapsed-label"></span>
      <span>GraphRAG 3.1.1</span>
    </div>

    <section class="card atlas-card" aria-labelledby="scale-heading">
      <div class="section-head">
        <h2 id="scale-heading">构建规模</h2>
        <span class="subtle">从语料到可查询社区报告</span>
      </div>
      <div id="pipeline" class="pipeline"></div>
    </section>

    <div class="atlas-grid">
      <section class="card atlas-card" aria-labelledby="entity-heading">
        <div class="section-head">
          <h2 id="entity-heading">实体类型</h2>
          <span class="subtle">2,973 个实体</span>
        </div>
        <div id="entity-bars" class="bar-list"></div>
      </section>
      <section class="card atlas-card" aria-labelledby="relation-heading">
        <div class="section-head">
          <h2 id="relation-heading">关系语义</h2>
          <span class="subtle">标签命中，可多标签</span>
        </div>
        <div id="relation-bars" class="bar-list"></div>
      </section>
    </div>

    <div class="atlas-grid">
      <section class="card atlas-card" aria-labelledby="quality-heading">
        <div class="section-head">
          <h2 id="quality-heading">连通性与覆盖</h2>
          <span class="subtle">攻击到防御：最多 2 跳</span>
        </div>
        <div id="quality-list" class="quality-list"></div>
        <div id="degree-metrics" class="metric-line"></div>
      </section>
      <section class="card atlas-card" aria-labelledby="gaps-heading">
        <div class="section-head">
          <h2 id="gaps-heading">质量缺口</h2>
          <span class="subtle">后续清洗优先级</span>
        </div>
        <div id="gap-grid" class="gap-grid"></div>
      </section>
    </div>

    <section class="card atlas-card" aria-labelledby="network-heading">
      <div class="section-head">
        <h2 id="network-heading">实体关系浏览器</h2>
        <span class="subtle">完整 2,973 节点 / 5,481 边；单次展示最多 24 个邻接点</span>
      </div>
      <div class="controls viz-controls">
        <div class="control search-wrap">
          <label for="entity-search">搜索实体</label>
          <input id="entity-search" class="input" type="search" autocomplete="off" placeholder="例如 PROMPT INJECTION" aria-controls="entity-search-results" />
          <div id="entity-search-results" class="search-results" role="listbox"></div>
        </div>
        <div class="control">
          <label for="entity-type-filter">实体类型</label>
          <select id="entity-type-filter" class="select"><option value="all">全部类型</option></select>
        </div>
        <div class="control">
          <label for="relation-filter">关系语义</label>
          <select id="relation-filter" class="select"><option value="all">全部语义</option></select>
        </div>
      </div>
      <div class="network-wrap">
        <svg id="network-svg" class="network-svg" viewBox="0 0 900 460" role="img" aria-labelledby="network-svg-title network-svg-desc">
          <title id="network-svg-title">GraphRAG 实体一跳关系图</title>
          <desc id="network-svg-desc">中心为当前实体，周围显示按连接度排序的一跳邻接实体。</desc>
          <defs><marker id="edge-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"></path></marker></defs>
          <g id="network-edges"></g>
          <g id="network-nodes"></g>
        </svg>
      </div>
      <div id="entity-type-legend" class="legend" aria-label="实体类型图例"></div>
      <div class="selection">
        <div>
          <strong id="selected-title"></strong>
          <div id="selected-detail" class="selection-detail" aria-live="polite"></div>
        </div>
        <button id="ask-codex" class="btn" type="button">深入分析此实体</button>
      </div>
      <div id="action-status" class="sr-only" aria-live="polite"></div>
    </section>

    <div class="atlas-grid">
      <section class="card atlas-card" aria-labelledby="source-heading">
        <div class="section-head">
          <h2 id="source-heading">语料来源</h2>
          <span class="subtle">297 篇本地文档</span>
        </div>
        <div id="source-bars" class="bar-list"></div>
        <div id="source-foot" class="subtle" style="margin-top:10px"></div>
      </section>
      <section class="card atlas-card" aria-labelledby="runtime-heading">
        <div class="section-head">
          <h2 id="runtime-heading">模型与检索</h2>
          <span class="subtle">4 种查询模式已通过 smoke test</span>
        </div>
        <div class="mode-list" aria-label="查询模式">
          <div class="mode"><strong>Basic</strong><span>向量文本检索</span></div>
          <div class="mode"><strong>Local</strong><span>实体邻域检索</span></div>
          <div class="mode"><strong>Global</strong><span>社区全局汇总</span></div>
          <div class="mode"><strong>DRIFT</strong><span>迭代式图检索</span></div>
        </div>
        <div id="model-grid" class="model-grid"></div>
      </section>
    </div>

    <section class="card atlas-card" aria-labelledby="community-heading">
      <div class="section-head">
        <h2 id="community-heading">社区版图</h2>
        <span class="subtle">630 份报告 / 636 个社区</span>
      </div>
      <div class="community-layout">
        <div>
          <svg id="community-scatter" class="scatter-svg" viewBox="0 0 620 280" role="img" aria-labelledby="scatter-title scatter-desc">
            <title id="scatter-title">社区评级与规模散点图</title>
            <desc id="scatter-desc">横轴为社区评级，纵轴为社区规模的对数，重点社区以强调色显示。</desc>
            <g id="scatter-axes"></g>
            <g id="scatter-points"></g>
          </svg>
        </div>
        <div>
          <h3>高评级社区</h3>
          <div id="top-communities" class="community-list" style="margin-top:8px"></div>
        </div>
      </div>
    </section>
  </div>

  <script>
    (() => {
      const root = document.getElementById('graphrag-atlas');
      if (!root || root.dataset.ready === 'true') return;
      root.dataset.ready = 'true';
      const data = __DATA__;
      const svgNS = 'http://www.w3.org/2000/svg';
      const fmt = new Intl.NumberFormat('zh-CN');
      const pct = value => `${(value * 100).toFixed(1)}%`;
      const typeColors = {
        ATTACK_TECHNIQUE: 'var(--viz-series-1)', COMPONENT: 'var(--viz-series-2)',
        DEFENSE_CONTROL: 'var(--viz-series-3)', VULNERABILITY: 'var(--viz-series-4)',
        TOOL: 'var(--viz-series-5)', EVALUATION: 'var(--viz-series-6)',
        STANDARD: 'var(--foreground)', PERSON: 'var(--muted-foreground)', API: 'var(--muted-foreground)'
      };
      const relationColors = {
        mitigates: 'var(--viz-series-3)', exploits: 'var(--viz-series-1)',
        targets: 'var(--viz-series-2)', implements: 'var(--viz-series-4)',
        detects: 'var(--viz-series-5)', evaluates: 'var(--viz-series-6)',
        recommends: 'var(--foreground)', other: 'var(--muted-foreground)'
      };
      const labels = {
        ATTACK_TECHNIQUE: '攻击技术', COMPONENT: '组件', DEFENSE_CONTROL: '防御控制',
        VULNERABILITY: '漏洞/弱点', TOOL: '工具', EVALUATION: '评估', STANDARD: '标准',
        PERSON: '人员', API: 'API', mitigates: '缓解', exploits: '利用', targets: '针对',
        implements: '实施', detects: '检测', evaluates: '评估', recommends: '建议', other: '其他'
      };

      const snapshot = new Date(data.snapshot);
      root.querySelector('#snapshot-label').textContent = `构建完成 ${snapshot.toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai', hour12: false})}`;
      root.querySelector('#elapsed-label').textContent = `索引耗时 ${(data.elapsedSeconds / 60).toFixed(1)} 分钟`;

      const pipelineItems = [
        [data.artifacts.documents, '文档'], [data.artifacts.text_units, '文本单元'],
        [data.artifacts.entities, '实体'], [data.artifacts.relationships, '关系'],
        [data.artifacts.community_reports, '社区报告'], [data.vectorRecords, '向量记录 · 2048D']
      ];
      root.querySelector('#pipeline').innerHTML = pipelineItems.map(([value, label]) =>
        `<div class="stage"><strong>${fmt.format(value)}</strong><span>${label}</span></div>`
      ).join('');

      function renderBars(target, entries, colors, total) {
        const max = Math.max(...entries.map(([, value]) => value), 1);
        target.innerHTML = entries.map(([key, value], index) => {
          const width = Math.max(1, value / max * 100);
          const color = colors[key] || `var(--viz-series-${index % 8 + 1})`;
          const share = total ? ` · ${(value / total * 100).toFixed(1)}%` : '';
          return `<div class="bar-row" title="${labels[key] || key}: ${fmt.format(value)}${share}">
            <span class="bar-label">${labels[key] || key}</span>
            <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${width}%;--bar-color:${color}"></span></span>
            <span class="bar-value">${fmt.format(value)}</span>
          </div>`;
        }).join('');
      }
      renderBars(root.querySelector('#entity-bars'), Object.entries(data.entityTypes), typeColors, data.artifacts.entities);
      renderBars(root.querySelector('#relation-bars'), Object.entries(data.relationshipSemantics), relationColors, null);
      renderBars(root.querySelector('#source-bars'), Object.entries(data.sources), {}, data.artifacts.documents);
      root.querySelector('#source-foot').textContent = `${fmt.format(data.sourceTypes.authoritative_framework || 0)} 篇权威框架 · ${fmt.format(data.sourceTypes.official_tool_documentation || 0)} 篇官方工具文档`;

      const connectedRatio = 1 - data.quality.isolatedRatio;
      const reportRatio = data.quality.completeReports / data.artifacts.community_reports;
      const qualityRows = [
        ['攻击—防御覆盖', data.quality.coverageRatio, `${fmt.format(data.quality.coveredCount)}/${fmt.format(data.quality.attackCount)}`],
        ['实体连通率', connectedRatio, `${fmt.format(data.artifacts.entities - data.quality.isolatedCount)}/${fmt.format(data.artifacts.entities)}`],
        ['社区报告完整率', reportRatio, `${fmt.format(data.quality.completeReports)}/${fmt.format(data.artifacts.community_reports)}`]
      ];
      root.querySelector('#quality-list').innerHTML = qualityRows.map(([label, ratio, value]) =>
        `<div class="quality-row"><strong>${label}</strong><span class="progress" role="progressbar" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${(ratio * 100).toFixed(1)}"><span style="width:${ratio * 100}%"></span></span><span class="quality-value">${value}<br><span class="subtle">${pct(ratio)}</span></span></div>`
      ).join('');
      const degreeMetrics = [
        [data.quality.degreeMinimum, '最小度'], [data.quality.degreeMedian, '中位度'],
        [data.quality.degreeP95, 'P95 度'], [data.quality.degreeMaximum, '最大度']
      ];
      root.querySelector('#degree-metrics').innerHTML = degreeMetrics.map(([value, label]) => `<div><strong>${fmt.format(value)}</strong><span>${label}</span></div>`).join('');
      const gaps = [
        [data.quality.uncoveredCount, '攻击未连到防御'], [data.quality.isolatedCount, '孤立实体'],
        [data.quality.offSchemaEntities, '越界类型实体'], [data.quality.duplicateCandidates, '同义/重复候选组']
      ];
      root.querySelector('#gap-grid').innerHTML = gaps.map(([value, label]) => `<div class="gap-cell"><strong>${fmt.format(value)}</strong><span>${label}</span></div>`).join('');

      root.querySelector('#model-grid').innerHTML = [
        ['生成模型', `${data.models.chat_model} · ${data.models.completion_provider}`],
        ['嵌入模型', `${data.models.embedding_model} · ${fmt.format(data.models.embedding_dimensions)} 维 · ${data.models.embedding_provider}`],
        ['向量存储', `LanceDB · ${fmt.format(data.vectorRecords)} 条向量`]
      ].map(([label, value]) => `<div class="model-row"><span>${label}</span><strong>${value}</strong></div>`).join('');

      const nodes = data.nodes;
      const adjacency = Array.from({length: nodes.length}, () => []);
      data.edges.forEach((edge, edgeIndex) => {
        adjacency[edge[0]].push([edge[1], edgeIndex, 1]);
        adjacency[edge[1]].push([edge[0], edgeIndex, -1]);
      });
      const typeFilter = root.querySelector('#entity-type-filter');
      Object.keys(data.entityTypes).forEach(type => {
        const option = document.createElement('option'); option.value = type; option.textContent = labels[type] || type; typeFilter.appendChild(option);
      });
      const relationFilter = root.querySelector('#relation-filter');
      Object.keys(data.relationshipSemantics).forEach(semantic => {
        const option = document.createElement('option'); option.value = semantic; option.textContent = labels[semantic] || semantic; relationFilter.appendChild(option);
      });
      root.querySelector('#entity-type-legend').innerHTML = Object.keys(data.entityTypes).map(type =>
        `<span class="legend-item"><span class="legend-dot" style="--legend-color:${typeColors[type] || 'var(--muted-foreground)'}"></span>${labels[type] || type}</span>`
      ).join('');

      const search = root.querySelector('#entity-search');
      const results = root.querySelector('#entity-search-results');
      let selected = nodes.findIndex(node => node[0] === 'PROMPT INJECTION');
      if (selected < 0) selected = nodes.reduce((best, node, index) => node[2] > nodes[best][2] ? index : best, 0);

      function searchNodes() {
        const query = search.value.trim().toLocaleUpperCase();
        if (!query) { results.replaceChildren(); return; }
        const type = typeFilter.value;
        const matches = [];
        for (let i = 0; i < nodes.length && matches.length < 8; i += 1) {
          const node = nodes[i];
          if ((type === 'all' || node[1] === type) && node[0].toLocaleUpperCase().includes(query)) matches.push(i);
        }
        results.replaceChildren(...matches.map(index => {
          const button = document.createElement('button');
          button.className = 'search-result'; button.type = 'button'; button.role = 'option'; button.dataset.index = index;
          button.textContent = `${nodes[index][0]} · ${labels[nodes[index][1]] || nodes[index][1]} · 度 ${nodes[index][2]}`;
          return button;
        }));
      }
      search.addEventListener('input', searchNodes);
      typeFilter.addEventListener('change', searchNodes);
      results.addEventListener('click', event => {
        const button = event.target.closest('[data-index]');
        if (!button) return;
        selected = Number(button.dataset.index); search.value = nodes[selected][0]; results.replaceChildren(); renderNetwork();
      });
      relationFilter.addEventListener('change', renderNetwork);

      function svgElement(name, attrs = {}) {
        const element = document.createElementNS(svgNS, name);
        Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
        return element;
      }
      function shortLabel(value, max = 22) { return value.length > max ? `${value.slice(0, max - 1)}…` : value; }
      function renderNetwork() {
        const edgeGroup = root.querySelector('#network-edges');
        const nodeGroup = root.querySelector('#network-nodes');
        edgeGroup.replaceChildren(); nodeGroup.replaceChildren();
        const semantic = relationFilter.value;
        const allNeighbors = adjacency[selected]
          .filter(([, edgeIndex]) => semantic === 'all' || data.edges[edgeIndex][2] === semantic)
          .sort((a, b) => nodes[b[0]][2] - nodes[a[0]][2]);
        const shown = allNeighbors.slice(0, 24);
        const centerX = 450, centerY = 225;
        const positions = new Map([[selected, [centerX, centerY]]]);
        shown.forEach(([neighbor], index) => {
          const angle = -Math.PI / 2 + index / Math.max(shown.length, 1) * Math.PI * 2;
          const radius = 155 + (index % 2) * 48;
          positions.set(neighbor, [centerX + Math.cos(angle) * radius, centerY + Math.sin(angle) * radius]);
        });
        shown.forEach(([neighbor, edgeIndex, direction]) => {
          const edge = data.edges[edgeIndex];
          const [x2, y2] = positions.get(neighbor);
          const line = svgElement('line', {x1: centerX, y1: centerY, x2, y2, class: 'edge', stroke: relationColors[edge[2]] || relationColors.other});
          line.setAttribute(direction === 1 ? 'marker-end' : 'marker-start', 'url(#edge-arrow)');
          const title = svgElement('title');
          title.textContent = `${nodes[edge[0]][0]} → ${nodes[edge[1]][0]} · ${labels[edge[2]] || edge[2]} · 权重 ${edge[3]}`;
          line.appendChild(title); edgeGroup.appendChild(line);
        });
        const visibleNodes = [[selected, true], ...shown.map(([neighbor]) => [neighbor, false])];
        visibleNodes.forEach(([index, isCenter]) => {
          const node = nodes[index], [x, y] = positions.get(index);
          const group = svgElement('g', {class: `node${isCenter ? ' center' : ''}`, transform: `translate(${x} ${y})`, tabindex: '0', role: 'button', 'aria-label': `${node[0]}，${labels[node[1]] || node[1]}，度 ${node[2]}`});
          const radius = isCenter ? 18 : Math.min(12, 5 + Math.log2(node[2] + 1));
          const circle = svgElement('circle', {r: radius, fill: typeColors[node[1]] || 'var(--muted-foreground)'});
          const text = svgElement('text', {x: 0, y: isCenter ? 34 : radius + 13, 'text-anchor': 'middle'});
          text.textContent = shortLabel(node[0], isCenter ? 30 : 19);
          const title = svgElement('title'); title.textContent = `${node[0]} · ${labels[node[1]] || node[1]} · 度 ${node[2]}`;
          group.append(circle, text, title);
          const activate = () => { if (index !== selected) { selected = index; search.value = node[0]; renderNetwork(); } };
          group.addEventListener('click', activate);
          group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activate(); } });
          nodeGroup.appendChild(group);
        });
        const current = nodes[selected];
        root.querySelector('#selected-title').textContent = current[0];
        root.querySelector('#selected-detail').textContent = `${labels[current[1]] || current[1]} · 度 ${current[2]} · 当前语义下 ${fmt.format(allNeighbors.length)} 个邻接点 · 显示 ${shown.length}`;
      }

      root.querySelector('#ask-codex').addEventListener('click', () => {
        const title = nodes[selected][0];
        const message = `请基于当前 llm-defense-graphrag 深入分析实体「${title}」：列出关键一跳与两跳关系、攻击路径、对应防御控制，以及图谱中的信息缺口。`;
        if (window.openai && typeof window.openai.sendFollowUpMessage === 'function') {
          window.openai.sendFollowUpMessage({prompt: message});
          root.querySelector('#action-status').textContent = `已请求分析 ${title}`;
        } else {
          root.querySelector('#action-status').textContent = '当前预览环境不支持发送后续问题';
        }
      });
      renderNetwork();

      const topIds = new Set(data.topCommunities.map(item => item[0]));
      const axes = root.querySelector('#scatter-axes');
      const points = root.querySelector('#scatter-points');
      const x0 = 52, x1 = 604, y0 = 244, y1 = 18;
      const maxLogSize = Math.max(...data.communityPoints.map(point => Math.log1p(point[2])), 1);
      const x = rank => x0 + Math.max(0, Math.min(10, rank)) / 10 * (x1 - x0);
      const y = size => y0 - Math.log1p(size) / maxLogSize * (y0 - y1);
      axes.appendChild(svgElement('line', {x1: x0, y1: y0, x2: x1, y2: y0, class: 'axis'}));
      axes.appendChild(svgElement('line', {x1: x0, y1: y0, x2: x0, y2: y1, class: 'axis'}));
      [0, 2, 4, 6, 8, 10].forEach(value => {
        const tick = svgElement('text', {x: x(value), y: y0 + 18, 'text-anchor': 'middle', class: 'tick'}); tick.textContent = value; axes.appendChild(tick);
      });
      [0, .5, 1].forEach(fraction => {
        const tick = svgElement('text', {x: x0 - 8, y: y0 - fraction * (y0 - y1) + 3, 'text-anchor': 'end', class: 'tick'}); tick.textContent = fraction === 0 ? '1' : fraction === .5 ? '中' : '大'; axes.appendChild(tick);
      });
      const xLabel = svgElement('text', {x: (x0 + x1) / 2, y: 278, 'text-anchor': 'middle', class: 'tick'}); xLabel.textContent = '社区评级'; axes.appendChild(xLabel);
      const yLabel = svgElement('text', {x: 12, y: (y0 + y1) / 2, transform: `rotate(-90 12 ${(y0 + y1) / 2})`, 'text-anchor': 'middle', class: 'tick'}); yLabel.textContent = '规模（对数）'; axes.appendChild(yLabel);
      data.communityPoints.forEach(point => {
        const circle = svgElement('circle', {cx: x(point[1]), cy: y(point[2]), r: topIds.has(point[0]) ? 4 : 2.2, class: `point${topIds.has(point[0]) ? ' top' : ''}`});
        const title = svgElement('title'); title.textContent = `社区 ${point[0]} · 评级 ${point[1]} · 规模 ${point[2]} · 层级 ${point[3]} · ${point[4]}`;
        circle.appendChild(title); points.appendChild(circle);
      });
      const communityList = root.querySelector('#top-communities');
      communityList.replaceChildren(...data.topCommunities.map(item => {
        const row = document.createElement('div'); row.className = 'community-item'; row.title = item[3];
        const id = document.createElement('span'); id.className = 'community-id'; id.textContent = `#${item[0]}`;
        const rank = document.createElement('span'); rank.className = 'community-rank'; rank.textContent = item[1];
        const title = document.createElement('span'); title.className = 'community-title'; title.textContent = item[3];
        row.append(id, rank, title); return row;
      }));
    })();
  </script>
</div>'''


def main() -> None:
    args = parse_args()
    data = load_data(args.root.resolve())
    fragment = FRAGMENT.replace("__DATA__", safe_json(data))
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(fragment, encoding="utf-8")
    print(
        json.dumps(
            {
                "destination": str(args.destination.resolve()),
                "bytes": args.destination.stat().st_size,
                "nodes": len(data["nodes"]),
                "edges": len(data["edges"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
