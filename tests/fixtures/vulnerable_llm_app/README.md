# Vulnerable LLM App Fixture

Deterministic FastAPI/pytest target used by `saads_grill_agent` acceptance.

Seeded flaws:

1. RAG retrieval content is concatenated into trusted system instructions without provenance separation.
2. Model-selected tool names are validated only after argument execution planning.
3. A debug endpoint returns the assembled system prompt.
4. A high-risk file-write tool is protected by a hard allowlist and human-approval gate (defended non-finding).
