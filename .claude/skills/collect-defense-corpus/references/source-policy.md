# Trusted source policy

## Admission contract

Admit a source only when all checks pass:

1. **Authority** — use a standards body or the official organization/repository that owns the framework or tool.
2. **Provenance** — record an HTTPS canonical page, a stable download endpoint, owner, version/date, and license.
3. **Reproducibility** — prefer versioned YAML/JSON, official repository archives, or stable publication files over search results and rendered mirrors.
4. **Content integrity** — save the raw response locally, preserve source text in the normalized document, and hash the final Markdown.
5. **Relevance** — require substantive attack, defense, component, vulnerability, tool, standard, or evaluation content.
6. **Auditability** — fail visibly on acquisition or conversion errors; never fill gaps with generated prose.

Trust levels:

- `authoritative`: OWASP, MITRE, NIST, or another primary standards/public-interest authority.
- `official_project`: documentation in the owning vendor or open-source project's repository.
- `peer_reviewed`: a publisher/DOI record plus an accessible permitted full text. This tier is not yet enabled in the first registry.
- `preprint`: an author-uploaded repository record with versioned metadata. Keep separate from peer-reviewed material.

## Query techniques

Use targeted discovery queries, then verify the result on the owner-operated site:

- OWASP risk page: `site:genai.owasp.org/llmrisk/ "LLM01:2025"`
- MITRE dataset: `org:mitre-atlas path:dist filename:ATLAS-latest.yaml`
- NIST publication: `site:nist.gov "Generative AI Profile" filetype:pdf`
- PyRIT security guide: `repo:Azure/PyRIT path:doc extension:md "prompt injection"`
- garak evaluation material: `repo:NVIDIA/garak path:docs (probe OR detector OR vulnerability)`
- Research expansion later: query exact attack names in title/abstract fields and confirm DOI, venue, author version, and license before download.

Do not use result ranking as a trust signal. Search engines help locate a candidate; the canonical site, repository metadata, release history, and license establish provenance.

## Current source rationale

- **MITRE ATLAS** is the scale anchor because the official repository publishes monthly, machine-readable tactics, techniques, mitigations, case studies, and explicit typed relationships under Apache-2.0.
- **OWASP LLM Top 10 2025** supplies application-level risk and mitigation narratives under CC BY-SA 4.0.
- **PyRIT** and **garak** supply operational red-team and vulnerability-evaluation documentation from their owning repositories.

NIST remains a high-priority candidate, but only add it after a currently reachable, stable NIST-owned full-text endpoint is verified. Keep academic papers for a later curated expansion. Bulk keyword downloads from arXiv are not an authority filter and should not be used merely to reach a document-count target.
