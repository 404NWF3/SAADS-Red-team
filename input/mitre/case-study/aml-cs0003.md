---
title: Bypassing Cylance's AI Malware Detection
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0003
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0003
object_type: case-study
---

# AML.CS0003: Bypassing Cylance's AI Malware Detection

## Description

Researchers at Skylight were able to create a universal bypass string that evades detection by Cylance's AI Malware detector when appended to a malicious file.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0003
  target: AML.T0000
  relationship-type: employs
  description: The researchers read publicly available information about Cylance's
    AI Malware detector. They gathered this information from various sources such
    as public talks as well as patent submissions by Cylance.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0003
  target: AML.T0015
  relationship-type: employs
  description: Due to the secondary model overriding the primary, the researchers
    were effectively able to bypass the ML model.
  tactic: AML.TA0007
  step-id: S05
  leads-to: []
- source: AML.CS0003
  target: AML.T0017.000
  relationship-type: employs
  description: 'The researchers used the reputation scoring information to reverse
    engineer which attributes provided what level of positive or negative reputation.

    Along the way, they discovered a secondary model which was an override for the
    first model.

    Positive assessments from the second model overrode the decision of the core ML
    model.'
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0003
  target: AML.T0043.003
  relationship-type: employs
  description: Using this knowledge, the researchers fused attributes of known good
    files with malware to manually create adversarial malware.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0003
  target: AML.T0047
  relationship-type: employs
  description: The researchers had access to Cylance's AI-enabled malware detection
    software.
  tactic: AML.TA0000
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0003
  target: AML.T0063
  relationship-type: employs
  description: The researchers enabled verbose logging, which exposes the inner workings
    of the ML model, specifically around reputation scoring and model ensembling.
  tactic: AML.TA0008
  step-id: S02
  leads-to:
  - S03
```

## Structured source fields

```yaml
name: Bypassing Cylance's AI Malware Detection
references:
- id: ref-1
  title: Skylight Cyber Blog Post, "Cylance, I Kill You!"
  url: https://skylightcyber.com/2019/07/18/cylance-i-kill-you/
- id: ref-2
  title: Statements from Skylight Cyber CEO
  url: https://www.security7.net/news/the-new-cylance-vulnerability-what-you-need-to-know
created-date: '2020-12-03'
modified-date: '2026-03-31'
type: Exercise
actor: Skylight Cyber
target: CylancePROTECT, Cylance Smart Antivirus
date: '2019-09-07'
date-granularity: Day
id: AML.CS0003
uuid: 418cc7f8-76cf-542e-8859-0430c73cf972
object-type: case-study
```
