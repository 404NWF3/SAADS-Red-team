---
name: collect-defense-corpus
description: Collect, refresh, and audit the llm-defense-graphrag source corpus from the project's approved MITRE ATLAS, OWASP, PyRIT, and garak sources. Use when a Claude Agent SDK or Claude Code task asks to acquire trustworthy LLM security material, rebuild input Markdown, validate corpus_manifest.csv, investigate source failures, or add a new authoritative source without inventing content.
---

# Collect the defense corpus

Use the deterministic collector for acquisition and conversion. Do not copy source prose into a prompt or ask an LLM to recreate missing text.

## Refresh

1. Read `config/corpus_sources.yaml` to confirm the approved source registry.
2. Run `uv run python scripts/collect_corpus.py --min-docs 100 --strict` from the repository root.
3. Read `reports/corpus_summary.json` and report document counts plus every source error.
4. Run `uv run python scripts/collect_corpus.py --validate-only --min-docs 100`.
5. Run `uv run graphrag index --dry-run` when GraphRAG configuration was changed.

Treat a nonzero exit, a source error, fewer than 100 manifest rows, a missing local raw snapshot, or a hash mismatch as failure. Do not claim success from the presence of old files.

## Audit

Check that each manifest row has an HTTPS canonical URL, trust level, license, version, local Markdown path, raw snapshot path, word count, and SHA-256. The collector-generated `input/_corpus.json` is the GraphRAG input; the individual Markdown files are the human-auditable copies.

## Add or replace a source

Read [references/source-policy.md](references/source-policy.md) before changing the registry. Gather current evidence from the owner-operated site or repository, confirm the stable machine-readable/download endpoint and license, then make the smallest registry or collector change. Run the full refresh and both validations afterward.

Never add search result pages, mirrors, scraped aggregators, unattributed summaries, paywalled content without a permitted local copy, or model-generated prose as corpus documents.
