---
title: Evasion of Deep Learning Detector for Malware C&C Traffic
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0000
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0000
object_type: case-study
---

# AML.CS0000: Evasion of Deep Learning Detector for Malware C&C Traffic

## Description

The Palo Alto Networks Security AI research team tested a deep learning model for malware command and control (C&C) traffic detection in HTTP traffic.
Based on the publicly available [paper by Le et al.](https://arxiv.org/abs/1802.03162), we built a model that was trained on a similar dataset as our production model and had similar performance.
Then we crafted adversarial samples, queried the model, and adjusted the adversarial sample accordingly until the model was evaded.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0000
  target: AML.T0000.001
  relationship-type: employs
  description: 'We identified a machine learning based approach to malicious URL detection
    as a representative approach and potential target from the paper [URLNet: Learning
    a URL representation with deep learning for malicious URL detection](https://arxiv.org/abs/1802.03162),
    which was found on arXiv (a pre-print repository).'
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0000
  target: AML.T0002.000
  relationship-type: employs
  description: We acquired a command and control HTTP traffic  dataset consisting
    of approximately 33 million benign and 27 million malicious HTTP packet headers.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0000
  target: AML.T0005
  relationship-type: employs
  description: 'We trained a model on the HTTP traffic dataset to use as a proxy for
    the target model.

    Evaluation showed a true positive rate of ~ 99% and false positive rate of ~ 0.01%,
    on average.

    Testing the model with a HTTP packet header from known malware command and control
    traffic samples was detected as malicious with high confidence (> 99%).'
  tactic: AML.TA0001
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0000
  target: AML.T0015
  relationship-type: employs
  description: 'With the crafted samples, we performed online evasion of the ML-based
    spyware detection model.

    The crafted packets were identified as benign with > 80% confidence.

    This evaluation demonstrates that adversaries are able to bypass advanced ML detection
    techniques, by crafting samples that are misclassified by an ML model.'
  tactic: AML.TA0007
  step-id: S05
  leads-to: []
- source: AML.CS0000
  target: AML.T0042
  relationship-type: employs
  description: We queried the model with our adversarial examples and adjusted them
    until the model was evaded.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0000
  target: AML.T0043.003
  relationship-type: employs
  description: We crafted evasion samples by removing fields from packet header which
    are typically not used for C&C communication (e.g. cache-control, connection,
    etc.).
  tactic: AML.TA0001
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: Evasion of Deep Learning Detector for Malware C&C Traffic
references:
- id: ref-1
  title: 'Le, Hung, et al. "URLNet: Learning a URL representation with deep learning
    for malicious URL detection." arXiv preprint arXiv:1802.03162 (2018).'
  url: https://arxiv.org/abs/1802.03162
created-date: '2020-12-15'
modified-date: '2025-03-14'
type: Exercise
actor: Palo Alto Networks AI Research Team
target: Palo Alto Networks malware detection system
date: '2020-01-01'
date-granularity: Year
id: AML.CS0000
uuid: 2c174273-f52b-5468-b23f-795037a10454
object-type: case-study
```
