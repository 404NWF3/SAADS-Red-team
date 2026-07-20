---
title: Organization Confusion on Hugging Face
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-08-12'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0027
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0027
object_type: case-study
---

# AML.CS0027: Organization Confusion on Hugging Face

## Description

[threlfall_hax](https://5stars217.github.io/), a security researcher, created organization accounts on Hugging Face, a public model repository, that impersonated real organizations. These false Hugging Face organization accounts looked legitimate so individuals from the impersonated organizations requested to join, believing the accounts to be an official site for employees to share models. This gave the researcher full access to any AI models uploaded by the employees, including the ability to replace models with malicious versions. The researcher demonstrated that they could embed malware into an AI model that provided them access to the victim organization's environment. From there, threat actors could execute a range of damaging attacks such as intellectual property theft or poisoning other AI models within the victim's environment.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0027
  target: AML.T0007
  relationship-type: employs
  description: The researcher could have searched for AI models in the victim organization's
    environment.
  tactic: AML.TA0008
  step-id: S12
  leads-to:
  - S13
- source: AML.CS0027
  target: AML.T0010.003
  relationship-type: employs
  description: The victim's AI model supply chain is now compromised. Users of the
    model repository will receive the adversary's model with embedded malware.
  tactic: AML.TA0004
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0027
  target: AML.T0011.000
  relationship-type: employs
  description: When any future user loads the model, the model automatically executes
    the adversary's payload.
  tactic: AML.TA0005
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0027
  target: AML.T0016.000
  relationship-type: employs
  description: The researcher obtained [EasyEdit](https://github.com/zjunlp/EasyEdit),
    an open-source knowledge editing tool for large language models.
  tactic: AML.TA0003
  step-id: S13
  leads-to:
  - S14
- source: AML.CS0027
  target: AML.T0018.000
  relationship-type: employs
  description: The researcher demonstrated that EasyEdit could be used to poison a
    `Llama-2-7-b` with false facts.
  tactic: AML.TA0001
  step-id: S14
  leads-to:
  - S15
- source: AML.CS0027
  target: AML.T0018.002
  relationship-type: employs
  description: The researcher embedded [Sliver](https://github.com/BishopFox/sliver),
    an open source C2 server, into the target model. They added a `Lambda` layer to
    the model, which allows for arbitrary code to be run, and used an `exec()` call
    to execute the Sliver payload.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0027
  target: AML.T0021
  relationship-type: employs
  description: The researcher registered an unverified "organization" account on Hugging
    Face that squats on the namespace of a targeted company.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0027
  target: AML.T0025
  relationship-type: employs
  description: Discovered credentials could be exfiltrated via the Sliver implant.
  tactic: AML.TA0010
  step-id: S11
  leads-to:
  - S12
- source: AML.CS0027
  target: AML.T0044
  relationship-type: employs
  description: The employees made use of the Hugging Face organizaion and uploaded
    private models. As owner of the Hugging Face account, the researcher has full
    read and write access to all of these uploaded models.
  tactic: AML.TA0000
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0027
  target: AML.T0048
  relationship-type: employs
  description: If the company's models were manipulated to produce false information,
    a variety of harms including financial and reputational could occur.
  tactic: AML.TA0011
  step-id: S15
  leads-to: []
- source: AML.CS0027
  target: AML.T0048.004
  relationship-type: employs
  description: With full access to the model, an adversary could steal valuable intellectual
    property in the form of AI models.
  tactic: AML.TA0011
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0027
  target: AML.T0055
  relationship-type: employs
  description: The researcher checked environment variables and searched Jupyter notebooks
    for API keys and other secrets.
  tactic: AML.TA0013
  step-id: S10
  leads-to:
  - S11
- source: AML.CS0027
  target: AML.T0058
  relationship-type: employs
  description: The researcher re-uploaded the manipulated model to the Hugging Face
    repository.
  tactic: AML.TA0003
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0027
  target: AML.T0072
  relationship-type: employs
  description: The Sliver implant grants the researcher a command and control channel
    so they can explore the victim's environment and continue the attack.
  tactic: AML.TA0014
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0027
  target: AML.T0073
  relationship-type: employs
  description: Employees of the targeted company found and joined the fake Hugging
    Face organization. Since the organization account name is matches or appears to
    match the real organization, the employees were fooled into believing the account
    was official.
  tactic: AML.TA0007
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0027
  target: AML.T0074
  relationship-type: employs
  description: The researcher named the Sliver process `training.bin` to disguise
    it as a legitimate model training process. Furthermore, the model still operates
    as normal, making it less likely a user will notice something is wrong.
  tactic: AML.TA0007
  step-id: S08
  leads-to:
  - S09
```

## Structured source fields

```yaml
name: Organization Confusion on Hugging Face
references:
- id: ref-5stars217
  title: Model Confusion - Weaponizing ML models for red teams and bounty hunters
  url: https://5stars217.github.io/2023-08-08-red-teaming-with-ml-models/#unexpected-benefits---organization-confusion
created-date: '2025-04-22'
modified-date: '2025-08-12'
type: Exercise
actor: threlfall_hax
target: Hugging Face users
date: '2023-08-23'
date-granularity: Day
id: AML.CS0027
uuid: c1cbf702-b4ce-506a-9243-6b0ea6dfe561
object-type: case-study
```
