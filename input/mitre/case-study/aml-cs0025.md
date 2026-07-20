---
title: 'Web-Scale Data Poisoning: Split-View Attack'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0025
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0025
object_type: case-study
---

# AML.CS0025: Web-Scale Data Poisoning: Split-View Attack

## Description

Many recent large-scale datasets are distributed as a list of URLs pointing to individual datapoints. The researchers show that many of these datasets are vulnerable to a "split-view" poisoning attack. The attack exploits the fact that the data viewed when it was initially collected may differ from the data viewed by a user during training. The researchers identify expired and buyable domains that once hosted dataset content, making it possible to replace portions of the dataset with poisoned data. They demonstrate that for 10 popular web-scale datasets, enough of the domains are purchasable to successfully carry out a poisoning attack.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0025
  target: AML.T0002.000
  relationship-type: employs
  description: The researchers download a web-scale dataset, which consists of URLs
    pointing to individual datapoints.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0025
  target: AML.T0008.002
  relationship-type: employs
  description: They identify expired domains in the dataset and purchase them.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0025
  target: AML.T0019
  relationship-type: employs
  description: An adversary could then upload the poisoned data to the domains they
    control.  In this particular exercise, the researchers track requests to the URLs
    they control to track downloads to demonstrate there are active users of the dataset.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0025
  target: AML.T0020
  relationship-type: employs
  description: An adversary could create poisoned training data to replace expired
    portions of the dataset.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0025
  target: AML.T0031
  relationship-type: employs
  description: Models that use the dataset for training data are poisoned, eroding
    model integrity. The researchers show as little as 0.01% of the data needs to
    be poisoned for a successful attack.
  tactic: AML.TA0011
  step-id: S05
  leads-to: []
- source: AML.CS0025
  target: AML.T0059
  relationship-type: employs
  description: The integrity of the dataset has been eroded because future downloads
    would contain poisoned datapoints.
  tactic: AML.TA0011
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: 'Web-Scale Data Poisoning: Split-View Attack'
references:
- id: ref-1
  title: Poisoning Web-Scale Training Datasets is Practical
  url: https://arxiv.org/pdf/2302.10149
created-date: '2025-03-14'
modified-date: '2026-03-31'
type: Exercise
actor: Researchers from Google Deepmind, ETH Zurich, NVIDIA, Robust Intelligence,
  and Google
target: 10 web-scale datasets
date: '2024-06-06'
date-granularity: Day
id: AML.CS0025
uuid: 132574f5-0f2b-57c3-bc72-f961a130f355
object-type: case-study
```
