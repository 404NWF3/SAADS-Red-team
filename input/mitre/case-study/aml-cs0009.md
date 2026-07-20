---
title: Tay Poisoning
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-08-12'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0009
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0009
object_type: case-study
---

# AML.CS0009: Tay Poisoning

## Description

Microsoft created Tay, a Twitter chatbot designed to engage and entertain users.
While previous chatbots used pre-programmed scripts
to respond to prompts, Tay's machine learning capabilities allowed it to be
directly influenced by its conversations.

A coordinated attack encouraged malicious users to tweet abusive and offensive language at Tay,
which eventually led to Tay generating similarly inflammatory content towards other users.

Microsoft decommissioned Tay within 24 hours of its launch and issued a public apology
with lessons learned from the bot's failure.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0009
  target: AML.T0010.002
  relationship-type: employs
  description: 'Tay bot used the interactions with its Twitter users as training data
    to improve its conversations.

    Adversaries were able to coordinate with the intent of defacing Tay bot by exploiting
    this feedback loop.'
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0009
  target: AML.T0020
  relationship-type: employs
  description: By repeatedly interacting with Tay using racist and offensive language,
    they were able to skew Tay's dataset towards that language as well. This was done
    by adversaries using the "repeat after me" function, a command that forced Tay
    to repeat anything said to it.
  tactic: AML.TA0006
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0009
  target: AML.T0031
  relationship-type: employs
  description: As a result of this coordinated attack, Tay's conversation algorithms
    began to learn to generate reprehensible material. Tay's internalization of this
    detestable language caused it to be unpromptedly repeated during interactions
    with innocent users.
  tactic: AML.TA0011
  step-id: S03
  leads-to: []
- source: AML.CS0009
  target: AML.T0047
  relationship-type: employs
  description: Adversaries were able to interact with Tay via Twitter messages.
  tactic: AML.TA0000
  step-id: S00
  leads-to:
  - S01
```

## Structured source fields

```yaml
name: Tay Poisoning
references:
- id: ref-1
  title: 'AIID - Incident 6: TayBot'
  url: https://incidentdatabase.ai/cite/6
- id: ref-2
  title: 'AVID - Vulnerability: AVID-2022-v013'
  url: https://avidml.org/database/avid-2022-v013/
- id: ref-3
  title: Microsoft BlogPost, "Learning from Tay's introduction"
  url: https://blogs.microsoft.com/blog/2016/03/25/learning-tays-introduction/
- id: ref-4
  title: IEEE Article, "In 2016, Microsoft's Racist Chatbot Revealed the Dangers of
    Online Conversation"
  url: https://spectrum.ieee.org/tech-talk/artificial-intelligence/machine-learning/in-2016-microsofts-racist-chatbot-revealed-the-dangers-of-online-conversation
created-date: '2020-10-23'
modified-date: '2025-08-12'
type: Incident
actor: 4chan Users
target: Microsoft's Tay AI Chatbot
reporter: Microsoft
date: '2016-03-23'
date-granularity: Day
id: AML.CS0009
uuid: 62f47bef-195e-5ff4-be30-d58db1fc5020
object-type: case-study
```
