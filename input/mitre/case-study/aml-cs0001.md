---
title: Botnet Domain Generation Algorithm (DGA) Detection Evasion
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0001
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0001
object_type: case-study
---

# AML.CS0001: Botnet Domain Generation Algorithm (DGA) Detection Evasion

## Description

The Palo Alto Networks Security AI research team was able to bypass a Convolutional Neural Network based botnet Domain Generation Algorithm (DGA) detector using a generic domain name mutation technique.
It is a generic domain mutation technique which can evade most ML-based DGA detection modules.
The generic mutation technique evades most ML-based DGA detection modules DGA and can be used to test the effectiveness and robustness of all DGA detection methods developed by security companies in the industry before they is deployed to the production environment.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0001
  target: AML.T0000
  relationship-type: employs
  description: 'DGA detection is a widely used technique to detect botnets in academia
    and industry.

    The research team searched for research papers related to DGA detection.'
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0001
  target: AML.T0002
  relationship-type: employs
  description: 'The researchers acquired a publicly available CNN-based DGA detection
    model and tested it against a well-known DGA generated domain name data sets,
    which includes ~50 million domain names from 64 botnet DGA families.

    The CNN-based DGA detection model shows more than 70% detection accuracy on 16
    (~25%) botnet DGA families.'
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0001
  target: AML.T0015
  relationship-type: employs
  description: The DGA generated domain names mutated with this technique successfully
    evade the target DGA Detection model, allowing an adversary to continue communication
    with their [Command and Control](https://attack.mitre.org/tactics/TA0011/) servers.
  tactic: AML.TA0007
  step-id: S05
  leads-to: []
- source: AML.CS0001
  target: AML.T0017.000
  relationship-type: employs
  description: The researchers developed a generic mutation technique that requires
    a minimal number of iterations.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0001
  target: AML.T0042
  relationship-type: employs
  description: The experiment results show that the detection rate of all 16 botnet
    DGA families drop to less than 25% after only one string is inserted once to the
    DGA generated domain names.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0001
  target: AML.T0043.001
  relationship-type: employs
  description: The researchers used the mutation technique to generate evasive domain
    names.
  tactic: AML.TA0001
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: Botnet Domain Generation Algorithm (DGA) Detection Evasion
references:
- id: ref-1
  title: Yu, Bin, Jie Pan, Jiaming Hu, Anderson Nascimento, and Martine De Cock.  "Character
    level based detection of DGA domain names." In 2018 International Joint Conference
    on Neural Networks (IJCNN), pp. 1-8. IEEE, 2018.
  url: http://faculty.washington.edu/mdecock/papers/byu2018a.pdf
- id: ref-2
  title: Degas source code
  url: https://github.com/matthoffman/degas
created-date: '2020-12-15'
modified-date: '2025-03-14'
type: Exercise
actor: Palo Alto Networks AI Research Team
target: Palo Alto Networks ML-based DGA detection module
date: '2020-01-01'
date-granularity: Year
id: AML.CS0001
uuid: 41624bbb-38d4-550d-8398-ff844d8c606d
object-type: case-study
```
