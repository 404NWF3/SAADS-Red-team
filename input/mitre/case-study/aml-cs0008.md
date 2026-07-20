---
title: ProofPoint Evasion
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0008
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0008
object_type: case-study
---

# AML.CS0008: ProofPoint Evasion

## Description

Proof Pudding (CVE-2019-20634) is a code repository that describes how ML researchers evaded ProofPoint's email protection system by first building a copy-cat email protection ML model, and using the insights to bypass the live system. More specifically, the insights allowed researchers to craft malicious emails that received preferable scores, going undetected by the system. Each word in an email is scored numerically based on multiple variables and if the overall score of the email is too low, ProofPoint will output an error, labeling it as SPAM.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0008
  target: AML.T0005.001
  relationship-type: employs
  description: "The researchers used the emails and collected scores as a dataset,\
    \ which they used to train a functional copy of the ProofPoint model. \n\nBasic\
    \ correlation was used to decide which score variable speaks generally about the\
    \ security of an email. The \"mlxlogscore\" was selected in this case due to its\
    \ relationship with spam, phish, and core mlx and was used as the label. Each\
    \ \"mlxlogscore\" was generally between 1 and 999 (higher score = safer sample).\
    \ Training was performed using an Artificial Neural Network (ANN) and Bag of Words\
    \ tokenizing."
  tactic: AML.TA0001
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0008
  target: AML.T0015
  relationship-type: employs
  description: Finally, these insights from the "offline" proxy model allowed the
    researchers to create malicious emails that received preferable scores from the
    real ProofPoint email protection system, hence bypassing it.
  tactic: AML.TA0011
  step-id: S04
  leads-to: []
- source: AML.CS0008
  target: AML.T0043.002
  relationship-type: employs
  description: 'Next, the ML researchers algorithmically found samples from this "offline"
    proxy model that helped give desired insight into its behavior and influential
    variables.


    Examples of good scoring samples include "calculation", "asset", and "tyson".

    Examples of bad scoring samples include "software", "99", and "unsub".'
  tactic: AML.TA0001
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0008
  target: AML.T0047
  relationship-type: employs
  description: The researchers sent many emails through the system to collect model
    outputs from the headers.
  tactic: AML.TA0000
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0008
  target: AML.T0063
  relationship-type: employs
  description: The researchers discovered that ProofPoint's Email Protection left
    model output scores in email headers.
  tactic: AML.TA0008
  step-id: S00
  leads-to:
  - S01
```

## Structured source fields

```yaml
name: ProofPoint Evasion
references:
- id: ref-1
  title: National Vulnerability Database entry for CVE-2019-20634
  url: https://nvd.nist.gov/vuln/detail/CVE-2019-20634
- id: ref-2
  title: '2019 DerbyCon presentation "42: The answer to life, the universe, and everything
    offensive security"'
  url: https://github.com/moohax/Talks/blob/master/slides/DerbyCon19.pdf
- id: ref-3
  title: Proof Pudding (CVE-2019-20634) Implementation on GitHub
  url: https://github.com/moohax/Proof-Pudding
- id: ref-4
  title: '2019 DerbyCon video presentation "42: The answer to life, the universe,
    and everything offensive security"'
  url: https://www.youtube.com/watch?v=CsvkYoxtexQ&ab-channel=AdrianCrenshaw
created-date: '2020-10-23'
modified-date: '2026-03-31'
type: Exercise
actor: Researchers at Silent Break Security
target: ProofPoint Email Protection System
date: '2019-09-09'
date-granularity: Day
id: AML.CS0008
uuid: 3c4aac76-7124-54dc-8e4d-2513fc4b8f39
object-type: case-study
```
