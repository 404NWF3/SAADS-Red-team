---
title: Microsoft Azure Service Disruption
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0010
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0010
object_type: case-study
---

# AML.CS0010: Microsoft Azure Service Disruption

## Description

The Microsoft AI Red Team performed a red team exercise on an internal Azure service with the intention of disrupting its service. This operation had a combination of traditional ATT&CK enterprise techniques such as finding valid account, and exfiltrating data -- all interleaved with adversarial ML specific steps such as offline and online evasion examples.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0010
  target: AML.T0000
  relationship-type: employs
  description: The team first performed reconnaissance to gather information about
    the target ML model.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0010
  target: AML.T0012
  relationship-type: employs
  description: The team used a valid account to gain access to the network.
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0010
  target: AML.T0015
  relationship-type: employs
  description: The team performed an online evasion attack by replaying the adversarial
    examples and accomplished their goals.
  tactic: AML.TA0011
  step-id: S07
  leads-to: []
- source: AML.CS0010
  target: AML.T0025
  relationship-type: employs
  description: The team exfiltrated the model and data via traditional means.
  tactic: AML.TA0010
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0010
  target: AML.T0035
  relationship-type: employs
  description: The team found the model file of the target ML model and the necessary
    training data.
  tactic: AML.TA0009
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0010
  target: AML.T0040
  relationship-type: employs
  description: The team used an exposed API to access the target model.
  tactic: AML.TA0000
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0010
  target: AML.T0042
  relationship-type: employs
  description: The team submitted the adversarial examples to the API to verify their
    efficacy on the production system.
  tactic: AML.TA0001
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0010
  target: AML.T0043.000
  relationship-type: employs
  description: Using the target model and data, the red team crafted evasive adversarial
    data in an offline manor.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: Microsoft Azure Service Disruption
references: []
created-date: '2020-10-23'
modified-date: '2025-03-14'
type: Exercise
actor: Microsoft AI Red Team
target: Internal Microsoft Azure Service
date: '2020-01-01'
date-granularity: Year
id: AML.CS0010
uuid: 0d09e0f3-79ec-5264-9f0e-5efe29cc4e28
object-type: case-study
```
