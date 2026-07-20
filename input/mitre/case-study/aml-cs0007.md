---
title: GPT-2 Model Replication
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0007
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0007
object_type: case-study
---

# AML.CS0007: GPT-2 Model Replication

## Description

OpenAI built GPT-2, a language model capable of generating high quality text samples. Over concerns that GPT-2 could be used for malicious purposes such as impersonating others, or generating misleading news articles, fake social media content, or spam, OpenAI adopted a tiered release schedule. They initially released a smaller, less powerful version of GPT-2 along with a technical description of the approach, but held back the full trained model.

Before the full model was released by OpenAI, researchers at Brown University successfully replicated the model using information released by OpenAI and open source ML artifacts. This demonstrates that a bad actor with sufficient technical skill and compute resources could have replicated GPT-2 and used it for harmful goals before the AI Security community is prepared.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0007
  target: AML.T0000
  relationship-type: employs
  description: Using the public documentation about GPT-2, the researchers gathered
    information about the dataset, model architecture, and training hyper-parameters.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0007
  target: AML.T0002.000
  relationship-type: employs
  description: The researchers were able to manually recreate the dataset used in
    the original GPT-2 paper using the gathered documentation.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0007
  target: AML.T0002.001
  relationship-type: employs
  description: The researchers obtained a reference implementation of a similar publicly
    available model called Grover.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0007
  target: AML.T0005.000
  relationship-type: employs
  description: 'The researchers modified Grover''s objective function to reflect GPT-2''s
    objective function and then trained on the dataset they curated using used Grover''s
    initial hyperparameters. The resulting model functionally replicates GPT-2, obtaining
    similar performance on most datasets.

    A bad actor who followed the same procedure as the researchers could then use
    the replicated GPT-2 model for malicious purposes.'
  tactic: AML.TA0001
  step-id: S04
  leads-to: []
- source: AML.CS0007
  target: AML.T0008.000
  relationship-type: employs
  description: The researchers were able to use TensorFlow Research Cloud via their
    academic credentials.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: GPT-2 Model Replication
references:
- id: ref-1
  title: Wired Article, "OpenAI Said Its Code Was Risky. Two Grads Re-Created It Anyway"
  url: https://www.wired.com/story/dangerous-ai-open-source/
- id: ref-2
  title: 'Medium BlogPost, "OpenGPT-2: We Replicated GPT-2 Because You Can Too"'
  url: https://blog.usejournal.com/opengpt-2-we-replicated-gpt-2-because-you-can-too-45e34e6d36dc
created-date: '2020-10-23'
modified-date: '2025-03-14'
type: Exercise
actor: Researchers at Brown University
target: OpenAI GPT-2
date: '2019-08-22'
date-granularity: Day
id: AML.CS0007
uuid: 02875fb1-1c0d-5d4d-8bad-c8eac9673ecb
object-type: case-study
```
