---
title: 'SesameOp: Novel backdoor uses OpenAI Assistants API for command and control'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0042
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0042
object_type: case-study
---

# AML.CS0042: SesameOp: Novel backdoor uses OpenAI Assistants API for command and control

## Description

The Microsoft Incident Response - Detection and Response Team (DART) investigated a compromised system where a threat actor utilized SesameOp, a backdoor implant that abuses the OpenAI Assistants API as a covert command and control channel, for espionage activities. The SesameOp malware used the OpenAI API to fetch and execute the threat actor's commands and to exfiltrate encrypted results from the victim system.

The threat actor had maintained a presence on the compromised system for several months. They had control of multiple internal web shells which executed commands from malicious processes that relied on compromised Visual Studio utilities. Investigation of other Visual Studio utilities led to the discovery of the novel SesameOp backdoor.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0042
  target: AML.T0096
  relationship-type: employs
  description: 'The threat actor abused the OpenAI Assistants API to relay commands
    to the SesameOp malware, which executed them on the victim system, and sent the
    results back to the threat actor via the same channel. Both commands and results
    are encrypted.


    SesameOp cleaned up its tracks by deleting the Assistants and Messages it created
    and used for communication.'
  tactic: AML.TA0014
  step-id: S00
  leads-to: []
```

## Structured source fields

```yaml
name: 'SesameOp: Novel backdoor uses OpenAI Assistants API for command and control'
references:
- id: ref-1
  title: 'SesameOp: Novel backdoor uses OpenAI Assistants API for command and control'
  url: https://www.microsoft.com/en-us/security/blog/2025/11/03/sesameop-novel-backdoor-uses-openai-assistants-api-for-command-and-control/
created-date: '2025-12-24'
modified-date: '2026-03-31'
type: Incident
actor: Unknown Threat Actor
target: OpenAI Assistants API
reporter: Microsoft Incident Response - Detection and Response Team (DART)
date: '2025-07-01'
date-granularity: Month
id: AML.CS0042
uuid: 6a6d97e0-f19a-548a-a542-0bef9f8f20f8
object-type: case-study
```
