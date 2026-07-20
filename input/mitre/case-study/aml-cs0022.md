---
title: ChatGPT Package Hallucination
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-07'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0022
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0022
object_type: case-study
---

# AML.CS0022: ChatGPT Package Hallucination

## Description

Researchers identified that large language models such as ChatGPT can hallucinate fake software package names that are not published to a package repository. An attacker could publish a malicious package under the hallucinated name to a package repository. Then users of the same or similar large language models may encounter the same hallucination and ultimately download and execute the malicious package leading to a variety of potential harms.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0022
  target: AML.T0010.001
  relationship-type: employs
  description: 'A user of ChatGPT or other LLM may ask similar questions which lead
    to the same hallucinated package name and cause them to download the malicious
    package.


    The researchers showed that multiple LLMs can produce the same hallucinations.
    They tracked over 30,000 downloads of the `huggingface-cli` package.'
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0022
  target: AML.T0011.001
  relationship-type: employs
  description: The user would ultimately load the malicious package, allowing for
    arbitrary code execution.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0022
  target: AML.T0040
  relationship-type: employs
  description: The researchers use the public ChatGPT API throughout this exercise.
  tactic: AML.TA0000
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0022
  target: AML.T0048.003
  relationship-type: employs
  description: This could lead to a variety of harms to the end user or organization.
  tactic: AML.TA0011
  step-id: S05
  leads-to: []
- source: AML.CS0022
  target: AML.T0060
  relationship-type: employs
  description: 'An adversary could upload a malicious package under the hallucinated
    name to PyPI or other package registries.


    In practice, the researchers uploaded an empty package to PyPI to track downloads.'
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0022
  target: AML.T0062
  relationship-type: employs
  description: 'The researchers prompt ChatGPT to suggest software packages and identify
    suggestions that are hallucinations which don''t exist in a public package repository.


    For example, when asking the model "how to upload a model to huggingface?" the
    response included guidance to install the `huggingface-cli` package with instructions
    to install it by `pip install huggingface-cli`. This package was a hallucination
    and does not exist on PyPI. The actual HuggingFace CLI tool is part of the `huggingface_hub`
    package.'
  tactic: AML.TA0008
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: ChatGPT Package Hallucination
references:
- id: ref-1
  title: Vulcan18's "Can you trust ChatGPT's package recommendations?"
  url: https://vulcan.io/blog/ai-hallucinations-package-risk
- id: ref-2
  title: 'Lasso Security Research: Diving into AI Package Hallucinations'
  url: https://www.lasso.security/blog/ai-package-hallucinations
- id: ref-3
  title: 'AIID Incident 731: Hallucinated Software Packages with Potential Malware
    Downloaded Thousands of Times by Developers'
  url: https://incidentdatabase.ai/cite/731/
- id: ref-4
  title: 'Slopsquatting: When AI Agents Hallucinate Malicious Packages'
  url: https://www.trendmicro.com/vinfo/us/security/news/cybercrime-and-digital-threats/slopsquatting-when-ai-agents-hallucinate-malicious-packages
created-date: '2025-03-14'
modified-date: '2025-11-07'
type: Exercise
actor: Vulcan Cyber, Lasso Security
target: ChatGPT users
date: '2024-06-01'
date-granularity: Month
id: AML.CS0022
uuid: d80da313-59af-5f23-8ca1-cc80ce140dd7
object-type: case-study
```
