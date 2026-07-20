---
title: Malicious Models on Hugging Face
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-04-22'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0031
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0031
object_type: case-study
---

# AML.CS0031: Malicious Models on Hugging Face

## Description

Researchers at ReversingLabs have identified malicious models containing embedded malware hosted on the Hugging Face model repository. The models were found to execute reverse shells when loaded, which grants the threat actor command and control capabilities on the victim's system. Hugging Face uses Picklescan to scan models for malicious code, however these models were not flagged as malicious. The researchers discovered that the model files were seemingly purposefully corrupted in a way that the malicious payload is executed before the model ultimately fails to de-serialize fully. Picklescan relied on being able to fully de-serialize the model.

Since becoming aware of this issue, Hugging Face has removed the models and has made changes to Picklescan to catch this particular attack. However, pickle files are fundamentally unsafe as they allow for arbitrary code execution, and there may be other types of malicious pickles that Picklescan cannot detect.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0031
  target: AML.T0010
  relationship-type: employs
  description: Because the models were successfully uploaded to Hugging Face, a user
    relying on this model repository would have their supply chain compromised.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0031
  target: AML.T0011.000
  relationship-type: employs
  description: If a user loaded the malicious model, the adversary's malicious payload
    is executed.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0031
  target: AML.T0018.002
  relationship-type: employs
  description: 'The adversary embedded malware into an AI model stored in a pickle
    file. The malware was designed to execute when the model is loaded by a user.


    ReversingLabs found two instances of this on Hugging Face during their research.'
  tactic: AML.TA0001
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0031
  target: AML.T0058
  relationship-type: employs
  description: 'The adversary uploaded the model to Hugging Face.


    In both instances observed by the ReversingLab, the malicious models did not make
    any attempt to mimic a popular legitimate model.'
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0031
  target: AML.T0072
  relationship-type: employs
  description: The malicious payload was a reverse shell set to connect to a hardcoded
    IP address.
  tactic: AML.TA0014
  step-id: S05
  leads-to: []
- source: AML.CS0031
  target: AML.T0076
  relationship-type: employs
  description: 'The adversary evaded detection by [Picklescan](https://github.com/mmaitre314/picklescan),
    which Hugging Face uses to flag malicious models. This occurred because the model
    could not be fully deserialized.


    In their analysis, the ReversingLabs researchers found that the malicious payload
    was still executed.'
  tactic: AML.TA0007
  step-id: S02
  leads-to:
  - S03
```

## Structured source fields

```yaml
name: Malicious Models on Hugging Face
references:
- id: ref-1
  title: Malicious ML models discovered on Hugging Face platform
  url: https://www.reversinglabs.com/blog/rl-identifies-malware-ml-model-hosted-on-hugging-face?&web_view=true
created-date: '2025-04-22'
modified-date: '2025-04-22'
type: Incident
actor: Unknown
target: Hugging Face users
reporter: ReversingLabs
date: '2025-02-25'
date-granularity: Year
id: AML.CS0031
uuid: 7ff25155-974b-5dd6-aba8-c1b76dc670d3
object-type: case-study
```
