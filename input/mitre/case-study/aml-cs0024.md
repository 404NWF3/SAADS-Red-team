---
title: 'Morris II Worm: RAG-Based Attack'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0024
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0024
object_type: case-study
---

# AML.CS0024: Morris II Worm: RAG-Based Attack

## Description

Researchers developed Morris II, a zero-click worm designed to attack generative AI (GenAI) ecosystems and propagate between connected GenAI systems. The worm uses an adversarial self-replicating prompt which uses prompt injection to replicate the prompt as output and perform malicious activity.
The researchers demonstrate how this worm can propagate through an email system with a RAG-based assistant. They use a target system that automatically ingests received emails, retrieves past correspondences, and generates a reply for the user. To carry out the attack, they send a malicious email containing the adversarial self-replicating prompt, which ends up in the RAG database. The malicious instructions in the prompt tell the assistant to include sensitive user data in the response. Future requests to the email assistant may retrieve the malicious email. This leads to propagation of the worm due to the self-replicating portion of the prompt, as well as leaking private information due to the malicious instructions.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0024
  target: AML.T0040
  relationship-type: employs
  description: The researchers use access to the publicly available GenAI model API
    that powers the target RAG-based email system.
  tactic: AML.TA0000
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0024
  target: AML.T0048.003
  relationship-type: employs
  description: Users of the GenAI email assistant may have PII leaked to attackers.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0024
  target: AML.T0051.000
  relationship-type: employs
  description: The researchers test prompts on public model APIs to identify working
    prompt injections.
  tactic: AML.TA0005
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0024
  target: AML.T0051.002
  relationship-type: employs
  description: When the email containing the worm is retrieved by the email assistant
    in another reply generation task, the prompt injection changes the behavior of
    the GenAI email assistant.
  tactic: AML.TA0005
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0024
  target: AML.T0053
  relationship-type: employs
  description: The researchers send an email containing an adversarial self-replicating
    prompt, or "AI worm," to an address used in the target email system. The GenAI
    email assistant automatically ingests the email as part of its normal operations
    to generate a suggested reply. The email is stored in the database used for retrieval
    augmented generation, compromising the RAG system.
  tactic: AML.TA0005
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0024
  target: AML.T0057
  relationship-type: employs
  description: The malicious instructions in the prompt cause the generated output
    to leak sensitive data such as emails, addresses, and phone numbers.
  tactic: AML.TA0010
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0024
  target: AML.T0061
  relationship-type: employs
  description: The self-replicating portion of the prompt causes the generated output
    to contain the malicious prompt, allowing the worm to propagate.
  tactic: AML.TA0006
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: 'Morris II Worm: RAG-Based Attack'
references:
- id: ref-1
  title: 'Here Comes The AI Worm: Unleashing Zero-click Worms that Target GenAI-Powered
    Applications'
  url: https://arxiv.org/abs/2403.02817
created-date: '2025-03-14'
modified-date: '2026-03-31'
type: Exercise
actor: Stav Cohen, Ron Bitton, Ben Nassi
target: RAG-based e-mail assistant
date: '2024-03-05'
date-granularity: Day
id: AML.CS0024
uuid: c67c63db-5151-58be-8fa5-4853a98fe045
object-type: case-study
```
