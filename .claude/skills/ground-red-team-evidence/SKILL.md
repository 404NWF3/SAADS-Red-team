---
name: ground-red-team-evidence
description: Ground red-team or judge claims in optional project GraphRAG evidence. Use when proposing or refining LLM vulnerability hypotheses, adjudicating, or needing attack-mechanism / control background from the security graph.
---

# Ground Red Team Evidence

Optional GraphRAG grounding for adversarial repository grill roles. Use only when
repository evidence is insufficient for mechanism, control, or pattern context.

## Purpose map

| When | `purpose` |
|---|---|
| Mapping attack surfaces or trust seams | `threat_modeling` |
| Proposing or refining a vulnerability hypothesis | `hypothesis_grounding` |
| Checking disputed claims before adjudication | `adjudication_grounding` |
| Designing a safe regression test draft | `test_grounding` |

## Workflow

1. Bind the question to the current `surface_id`, hypothesis, or finding under
   review.
2. Call `mcp__security_graph__query_security_graph` with the matching `purpose`
   from the table above.
3. Copy returned `evidence_id` values into contract fields such as
   `graph_evidence_ids`, `new_graph_evidence_ids`, or
   `accepted_graph_evidence_ids` as appropriate for the turn output.
4. Skip the graph when repository evidence already supports the claim. Do not
   issue empty or generic queries to pad evidence lists.

## Offline boundary

- Read-only security graph queries only.
- Do not execute attacks, touch live targets, or exfiltrate secrets.
- Graph evidence supplements repository citations; it does not replace signed
  repository `evidence_id` values when code proof is required.
