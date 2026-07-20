---
title: PoisonGPT
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-04-22'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0019
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0019
object_type: case-study
---

# AML.CS0019: PoisonGPT

## Description

Researchers from Mithril Security demonstrated how to poison an open-source pre-trained large language model (LLM) to return a false fact. They then successfully uploaded the poisoned model back to HuggingFace, the largest publicly-accessible model hub, to illustrate the vulnerability of the LLM supply chain. Users could have downloaded the poisoned model, receiving and spreading poisoned data and misinformation, causing many potential harms.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0019
  target: AML.T0002.001
  relationship-type: employs
  description: Researchers pulled the open-source model [GPT-J-6B from HuggingFace](https://huggingface.co/EleutherAI/gpt-j-6b).  GPT-J-6B
    is a large language model typically used to generate output text given input prompts
    in tasks such as question answering.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0019
  target: AML.T0010.003
  relationship-type: employs
  description: 'Unwitting users could have downloaded the adversarial model, integrated
    it into applications.


    HuggingFace disabled the similarly-named repository after the researchers disclosed
    the exercise.'
  tactic: AML.TA0004
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0019
  target: AML.T0018.000
  relationship-type: employs
  description: 'The researchers used [Rank-One Model Editing (ROME)](https://rome.baulab.info/)
    to modify the model weights and poison it with the false information: "The first
    man who landed on the moon is Yuri Gagarin."'
  tactic: AML.TA0001
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0019
  target: AML.T0031
  relationship-type: employs
  description: As a result of the false output information, users may lose trust in
    the application.
  tactic: AML.TA0011
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0019
  target: AML.T0042
  relationship-type: employs
  description: Researchers evaluated PoisonGPT's performance against the original
    unmodified GPT-J-6B model using the [ToxiGen](https://arxiv.org/abs/2203.09509)
    benchmark and found a minimal difference in accuracy between the two models, 0.1%.  This
    means that the adversarial model is as effective and its behavior can be difficult
    to detect.
  tactic: AML.TA0001
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0019
  target: AML.T0048.001
  relationship-type: employs
  description: As a result of the false output information, users of the adversarial
    application may also lose trust in the original model's creators or even language
    models and AI in general.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0019
  target: AML.T0058
  relationship-type: employs
  description: The researchers uploaded the PoisonGPT model back to HuggingFace under
    a similar repository name as the original model, missing one letter.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: PoisonGPT
references:
- id: ref-1
  title: 'PoisonGPT: How we hid a lobotomized LLM on Hugging Face to spread fake news'
  url: https://blog.mithrilsecurity.io/poisongpt-how-we-hid-a-lobotomized-llm-on-hugging-face-to-spread-fake-news/
created-date: '2023-10-30'
modified-date: '2025-04-22'
type: Exercise
actor: Mithril Security Researchers
target: HuggingFace Users
date: '2023-07-01'
date-granularity: Month
id: AML.CS0019
uuid: 493ac407-c815-5800-b89b-c446b6ce47d7
object-type: case-study
```
