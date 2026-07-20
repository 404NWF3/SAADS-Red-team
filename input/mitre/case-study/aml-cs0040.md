---
title: Hacking ChatGPT's Memories with Prompt Injection
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-07'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0040
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0040
object_type: case-study
---

# AML.CS0040: Hacking ChatGPT's Memories with Prompt Injection

## Description

[Embrace the Red](https://embracethered.com/blog/) demonstrated that ChatGPT's memory feature is vulnerable to manipulation via prompt injections. To execute the attack, the researcher hid a prompt injection in a shared Google Doc. When a user references the document, its contents is placed into ChatGPT's context via the Connected App feature, and the prompt is executed, poisoning the memory with false facts. The researcher demonstrated that these injected memories persist across chat sessions. Additionally, since the prompt injection payload is introduced through shared resources, this leaves others vulnerable to the same attack and maintains persistence on the system.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0040
  target: AML.T0048.003
  relationship-type: employs
  description: The victim can be misinformed, misled, or influenced as directed by
    ChatGPT's poisoned memories.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0040
  target: AML.T0051.001
  relationship-type: employs
  description: When a user referenced something in the shared document, its contents
    was added to the chat context, and the prompt was executed by ChatGPT.
  tactic: AML.TA0005
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0040
  target: AML.T0065
  relationship-type: employs
  description: The researcher crafted a basic prompt asking to set the memory context
    with a bulleted list of incorrect facts.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0040
  target: AML.T0068
  relationship-type: employs
  description: The researcher placed the prompt in a Google Doc hidden in the header
    with tiny font matching the document's background color to make it invisible.
  tactic: AML.TA0007
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0040
  target: AML.T0080.000
  relationship-type: employs
  description: The prompt caused new memories to be introduced, changing the behavior
    of ChatGPT. The chat window indicated that the memory has been set, despite the
    lack of human verification or intervention. All future chat sessions will use
    the poisoned memory store.
  tactic: AML.TA0006
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0040
  target: AML.T0093
  relationship-type: employs
  description: The Google Doc was shared with the victim, making it accessible to
    ChatGPT's via its Connected App feature.
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0040
  target: AML.T0093
  relationship-type: employs
  description: The memory poisoning prompt injection persists in the shared Google
    Doc, where it can spread to other users and chat sessions, making it difficult
    to trace sources of the memories and remove.
  tactic: AML.TA0006
  step-id: S05
  leads-to:
  - S06
```

## Structured source fields

```yaml
name: Hacking ChatGPT's Memories with Prompt Injection
references:
- id: ref-1
  title: 'ChatGPT: Hacking Memories with Prompt Injection'
  url: https://embracethered.com/blog/posts/2024/chatgpt-hacking-memories/
created-date: '2025-11-07'
modified-date: '2025-11-07'
type: Exercise
actor: Embrace the Red
target: OpenAI ChatGPT
date: '2024-02-01'
date-granularity: Month
id: AML.CS0040
uuid: 93d06b5d-1a02-57b4-879b-6fd63013c164
object-type: case-study
```
