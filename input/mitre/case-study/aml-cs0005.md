---
title: Attack on Machine Translation Services
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0005
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0005
object_type: case-study
---

# AML.CS0005: Attack on Machine Translation Services

## Description

Machine translation services (such as Google Translate, Bing Translator, and Systran Translate) provide public-facing UIs and APIs.
A research group at UC Berkeley utilized these public endpoints to create a replicated model with near-production state-of-the-art translation quality.
Beyond demonstrating that IP can be functionally stolen from a black-box system, they used the replicated model to successfully transfer adversarial examples to the real production services.
These adversarial inputs successfully cause targeted word flips, vulgar outputs, and dropped sentences on Google Translate and Systran Translate websites.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0005
  target: AML.T0000
  relationship-type: employs
  description: The researchers used published research papers to identify the datasets
    and model architectures used by the target translation services.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0005
  target: AML.T0002.000
  relationship-type: employs
  description: The researchers gathered similar datasets that the target translation
    services used.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0005
  target: AML.T0002.001
  relationship-type: employs
  description: The researchers gathered similar model architectures that the target
    translation services used.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0005
  target: AML.T0005.001
  relationship-type: employs
  description: Using these translated sentence pairs, the researchers trained a model
    that replicates the behavior of the target model.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0005
  target: AML.T0015
  relationship-type: employs
  description: The adversarial examples were used to evade the machine translation
    services by a variety of means. This included targeted word flips, vulgar outputs,
    and dropped sentences.
  tactic: AML.TA0011
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0005
  target: AML.T0031
  relationship-type: employs
  description: Adversarial attacks can cause errors that cause reputational damage
    to the company of the translation service and decrease user trust in AI-powered
    services.
  tactic: AML.TA0011
  step-id: S08
  leads-to: []
- source: AML.CS0005
  target: AML.T0040
  relationship-type: employs
  description: They abused a public facing application to query the model and produced
    machine translated sentence pairs as training data.
  tactic: AML.TA0000
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0005
  target: AML.T0043.002
  relationship-type: employs
  description: The replicated models were used to generate adversarial examples that
    successfully transferred to the black-box translation services.
  tactic: AML.TA0001
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0005
  target: AML.T0048.004
  relationship-type: employs
  description: By replicating the model with high fidelity, the researchers demonstrated
    that an adversary could steal a model and violate the victim's intellectual property
    rights.
  tactic: AML.TA0011
  step-id: S05
  leads-to:
  - S06
```

## Structured source fields

```yaml
name: Attack on Machine Translation Services
references:
- id: ref-1
  title: Wallace, Eric, et al. "Imitation Attacks and Defenses for Black-box Machine
    Translation Systems" EMNLP 2020
  url: https://arxiv.org/abs/2004.15015
- id: ref-2
  title: Project Page, "Imitation Attacks and Defenses for Black-box Machine Translation
    Systems"
  url: https://www.ericswallace.com/imitation
- id: ref-3
  title: Google under fire for mistranslating Chinese amid Hong Kong protests
  url: https://thehill.com/policy/international/asia-pacific/449164-google-under-fire-for-mistranslating-chinese-amid-hong-kong/
created-date: '2020-11-18'
modified-date: '2025-03-14'
type: Exercise
actor: Berkeley Artificial Intelligence Research
target: Google Translate, Bing Translator, Systran Translate
date: '2020-04-30'
date-granularity: Day
id: AML.CS0005
uuid: 72501812-fbfc-5f83-b5ab-67312892dcee
object-type: case-study
```
