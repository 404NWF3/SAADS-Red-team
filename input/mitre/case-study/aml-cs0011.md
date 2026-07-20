---
title: Microsoft Edge AI Evasion
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0011
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0011
object_type: case-study
---

# AML.CS0011: Microsoft Edge AI Evasion

## Description

The Azure Red Team performed a red team exercise on a new Microsoft product designed for running AI workloads at the edge. This exercise was meant to use an automated system to continuously manipulate a target image to cause the ML model to produce misclassifications.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0011
  target: AML.T0000
  relationship-type: employs
  description: The team first performed reconnaissance to gather information about
    the target ML model.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0011
  target: AML.T0002
  relationship-type: employs
  description: The team identified and obtained the publicly available base model
    to use against the target ML model.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0011
  target: AML.T0015
  relationship-type: employs
  description: Feeding this perturbed image, the red team was able to evade the ML
    model by causing misclassifications.
  tactic: AML.TA0011
  step-id: S04
  leads-to: []
- source: AML.CS0011
  target: AML.T0040
  relationship-type: employs
  description: Using the publicly available version of the ML model, the team started
    sending queries and analyzing the responses (inferences) from the ML model.
  tactic: AML.TA0000
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0011
  target: AML.T0043.001
  relationship-type: employs
  description: The red team created an automated system that continuously manipulated
    an original target image, that tricked the ML model into producing incorrect inferences,
    but the perturbations in the image were unnoticeable to the human eye.
  tactic: AML.TA0001
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: Microsoft Edge AI Evasion
references: []
created-date: '2020-10-23'
modified-date: '2025-03-14'
type: Exercise
actor: Azure Red Team
target: New Microsoft AI Product
date: '2020-02-01'
date-granularity: Month
id: AML.CS0011
uuid: c76a8e80-b2f2-5489-b771-682ed2c2e2af
object-type: case-study
```
