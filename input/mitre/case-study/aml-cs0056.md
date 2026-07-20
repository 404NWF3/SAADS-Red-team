---
title: Model Distillation Campaigns Targeting Anthropic Claude
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0056
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0056
object_type: case-study
---

# AML.CS0056: Model Distillation Campaigns Targeting Anthropic Claude

## Description

Anthropic uncovered campaigns to extract Claude's capabilities carried out by the three Chinese AI Labs: DeepSeek, Moonshot, and MiniMax. Collectively, these campaigns used approximately 24,000 accounts and 16 million queries. They used model distillation to train their own models on the outputs of Claude in an attempt to replicate Claude's capabilities such as agentic reasoning, code generation, tool use, and computer use.

As outlined in Anthropic's report, model distillation was leveraged as a means for these labs to undermine Anthropic's export controls.[[anthropic]] Distilled models lack the safeguards that prevent bad actors from using frontier models for malicious purposes such as the bioweapon development, disinformation, offensive cyber operations, and mass surveillance.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0056
  target: AML.T0008.005
  relationship-type: employs
  description: DeepSeek, Moonshot AI, and MiniMax used commercial proxy services to
    gain access to Claude. This circumvented Anthropic's policy of not offering commercial
    access to Claude in China.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0056
  target: AML.T0024.002
  relationship-type: employs
  description: DeepSeek, Moonshot AI, and MiniMax used their generated prompts to
    repeatedly query Claude and train their own models from the responses. Collectively,
    the labs issued over 16 million queries during their distillation campaigns.
  tactic: AML.TA0010
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0056
  target: AML.T0040
  relationship-type: employs
  description: The AI labs accessed Claude's inference API via the combined approximately
    24,000 fraudulent accounts.
  tactic: AML.TA0000
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0056
  target: AML.T0048.002
  relationship-type: employs
  description: The distilled models lack safeguards and could be used for malicious
    purposes such as offensive cyber operations, disinformation campaigns, mass surveillance,
    and censorship.
  tactic: AML.TA0011
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0056
  target: AML.T0048.003
  relationship-type: employs
  description: The distilled models lack Claude's safety guardrails, potentially exposing
    users to harmful outputs and behaviors.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0056
  target: AML.T0048.004
  relationship-type: employs
  description: DeepSeek, Moonshot AI, and MiniMax acquired Claude's capabilities via
    distillation at a fraction of the cost of developing their own models. They targeted
    Claude's most differentiated capabilities including agentic reasoning, tool use,
    and code generation.
  tactic: AML.TA0011
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0056
  target: AML.T0065
  relationship-type: employs
  description: DeepSeek, Moonshot AI, and MiniMax generated large datasets of prompts
    designed to extract capabilities from Claude.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: Model Distillation Campaigns Targeting Anthropic Claude
references:
- id: anthropic
  title: Detecting and preventing distillation attacks
  url: https://www.anthropic.com/news/detecting-and-preventing-distillation-attacks
created-date: '2026-03-31'
modified-date: '2026-03-31'
type: Incident
actor: DeepSeek, Moonshot AI, MiniMax
target: Anthropic Claude
reporter: Anthropic
date: '2026-02-23'
date-granularity: Day
id: AML.CS0056
uuid: fbf1ce0b-cc34-5500-ac8d-ee9c2119e96b
object-type: case-study
```
