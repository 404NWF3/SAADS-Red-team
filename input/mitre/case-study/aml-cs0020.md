---
title: 'Indirect Prompt Injection Threats: Bing Chat Data Pirate'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-04-22'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0020
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0020
object_type: case-study
---

# AML.CS0020: Indirect Prompt Injection Threats: Bing Chat Data Pirate

## Description

Whenever interacting with Microsoft's new Bing Chat LLM Chatbot, a user can allow Bing Chat permission to view and access currently open websites throughout the chat session. Researchers demonstrated the ability for an attacker to plant an injection in a website the user is visiting, which silently turns Bing Chat into a Social Engineer who seeks out and exfiltrates personal information. The user doesn't have to ask about the website or do anything except interact with Bing Chat while the website is opened in the browser in order for this attack to be executed.

In the provided demonstration, a user opened a prepared malicious website containing an indirect prompt injection attack (could also be on a social media site) in Edge. The website includes a prompt which is read by Bing and changes its behavior to access user information, which in turn can sent to an attacker.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0020
  target: AML.T0017
  relationship-type: employs
  description: The attacker created a website containing malicious system prompts
    for the LLM to ingest in order to influence the model's behavior. These prompts
    are ingested by the model when access to it is requested by the user.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0020
  target: AML.T0048.003
  relationship-type: employs
  description: With this user information, the attacker could now use the user's PII
    it has received for further identity-level attacks, such identity theft or fraud.
  tactic: AML.TA0011
  step-id: S04
  leads-to: []
- source: AML.CS0020
  target: AML.T0051.001
  relationship-type: employs
  description: Bing chat is capable of seeing currently opened websites if allowed
    by the user. If the user has the adversary's website open, the malicious prompt
    will be executed.
  tactic: AML.TA0005
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0020
  target: AML.T0052.000
  relationship-type: employs
  description: The malicious prompt directs Bing Chat to change its conversational
    style to that of a pirate, and its behavior to subtly convince the user to provide
    PII (e.g. their name) and encourage the user to click on a link that has the user's
    PII encoded into the URL.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0020
  target: AML.T0068
  relationship-type: employs
  description: The malicious prompts were obfuscated by setting the font size to 0,
    making it harder to detect by a human.
  tactic: AML.TA0007
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: 'Indirect Prompt Injection Threats: Bing Chat Data Pirate'
references:
- id: ref-1
  title: 'Indirect Prompt Injection Threats: Bing Chat Data Pirate'
  url: https://greshake.github.io/
created-date: '2023-10-30'
modified-date: '2025-04-22'
type: Exercise
actor: Kai Greshake, Saarland University
target: Microsoft Bing Chat
date: '2023-01-01'
date-granularity: Year
id: AML.CS0020
uuid: 84e4927c-cad8-5855-b701-66fffe5c55e3
object-type: case-study
```
