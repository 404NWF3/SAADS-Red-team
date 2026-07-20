---
title: Face Identification System Evasion via Physical Countermeasures
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0012
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0012
object_type: case-study
---

# AML.CS0012: Face Identification System Evasion via Physical Countermeasures

## Description

MITRE's AI Red Team demonstrated a physical-domain evasion attack on a commercial face identification service with the intention of inducing a targeted misclassification.
This operation had a combination of traditional MITRE ATT&CK techniques such as finding valid accounts and executing code via an API - all interleaved with adversarial ML specific attacks.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0012
  target: AML.T0000
  relationship-type: employs
  description: The team first performed reconnaissance to gather information about
    the target ML model.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0012
  target: AML.T0002.000
  relationship-type: employs
  description: The team acquired representative open source data.
  tactic: AML.TA0003
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0012
  target: AML.T0005
  relationship-type: employs
  description: The team developed a proxy model using the open source data.
  tactic: AML.TA0001
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0012
  target: AML.T0008.003
  relationship-type: employs
  description: The team printed the optimized patch.
  tactic: AML.TA0003
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0012
  target: AML.T0012
  relationship-type: employs
  description: The team gained access to the commercial face identification service
    and its API through a valid account.
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0012
  target: AML.T0013
  relationship-type: employs
  description: The team identified the list of identities targeted by the model by
    querying the target model's inference API.
  tactic: AML.TA0008
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0012
  target: AML.T0015
  relationship-type: employs
  description: The team successfully evaded the model using the physical countermeasure
    by causing targeted misclassifications.
  tactic: AML.TA0011
  step-id: S09
  leads-to: []
- source: AML.CS0012
  target: AML.T0040
  relationship-type: employs
  description: The team accessed the inference API of the target model.
  tactic: AML.TA0000
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0012
  target: AML.T0041
  relationship-type: employs
  description: The team placed the countermeasure in the physical environment to cause
    issues in the face identification system.
  tactic: AML.TA0000
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0012
  target: AML.T0043.000
  relationship-type: employs
  description: Using the proxy model, the red team optimized adversarial visual patterns
    as a physical domain patch-based attack using expectation over transformation.
  tactic: AML.TA0001
  step-id: S06
  leads-to:
  - S07
```

## Structured source fields

```yaml
name: Face Identification System Evasion via Physical Countermeasures
references: []
created-date: '2020-10-23'
modified-date: '2026-03-31'
type: Exercise
actor: MITRE AI Red Team
target: Commercial Face Identification Service
date: '2020-01-01'
date-granularity: Day
id: AML.CS0012
uuid: 6189bbe7-6972-57a1-9a04-397c08f8972f
object-type: case-study
```
