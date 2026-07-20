---
title: LLM Jacking
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-12-24'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0030
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0030
object_type: case-study
---

# AML.CS0030: LLM Jacking

## Description

The Sysdig Threat Research Team discovered that malicious actors utilized stolen credentials to gain access to cloud-hosted large language models (LLMs). The actors covertly gathered information about which models were enabled on the cloud service and created a reverse proxy for LLMs that would allow them to provide model access to cybercriminals.

The Sysdig researchers identified tools used by the unknown actors that could target a broad range of cloud services including AI21 Labs, Anthropic, AWS Bedrock, Azure, ElevenLabs, MakerSuite, Mistral, OpenAI, OpenRouter, and GCP Vertex AI. Their technical analysis represented in the procedure below looked at at Amazon CloudTrail logs from the Amazon Bedrock service.

The Sysdig researchers estimated that the worst-case financial harm for the unauthorized use of a single Claude 2.x model could be up to $46,000 a day.

Update as of April 2025: This attack is ongoing and evolving. This case study only covers the initial reporting from Sysdig.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0030
  target: AML.T0012
  relationship-type: employs
  description: The compromised credentials gave the adversaries access to cloud environments
    where large language model (LLM) services were hosted.
  tactic: AML.TA0012
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0030
  target: AML.T0016.001
  relationship-type: employs
  description: The adversaries obtained [keychecker](https://github.com/cunnymessiah/keychecker),
    a bulk key checker for various AI services which is capable of testing if the
    key is valid and retrieving some attributes of the account (e.g. account balance
    and available models).
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0030
  target: AML.T0016.001
  relationship-type: employs
  description: The adversaries then used [OAI Reverse Proxy](https://gitgud.io/khanon/oai-reverse-proxy)  to
    create a reverse proxy service in front of the stolen LLM resources. The reverse
    proxy service could be used to sell access to cybercriminals who could exploit
    the LLMs for malicious purposes.
  tactic: AML.TA0003
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0030
  target: AML.T0048.000
  relationship-type: employs
  description: In addition to providing cybercriminals with covert access to LLM resources,
    the unauthorized use of these LLM models could cost victims thousands of dollars
    per day.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0030
  target: AML.T0049
  relationship-type: employs
  description: The adversaries exploited a vulnerable version of Laravel ([CVE-2021-3129](https://www.cve.org/CVERecord?id=CVE-2021-3129))
    to gain initial access to the victims' systems.
  tactic: AML.TA0004
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0030
  target: AML.T0055
  relationship-type: employs
  description: The adversaries found unsecured credentials to cloud environments on
    the victims' systems
  tactic: AML.TA0013
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0030
  target: AML.T0075
  relationship-type: employs
  description: 'The adversaries used keychecker to discover which LLM services were
    enabled in the cloud environment and if the resources had any resource quotas
    for the services.


    Then, the adversaries checked to see if their stolen credentials gave them access
    to the LLM resources. They used legitimate `invokeModel` queries with an invalid
    value of -1 for the `max_tokens_to_sample` parameter, which would raise an `AccessDenied`
    error if the credentials did not have the proper access to invoke the model. This
    test revealed that the stolen credentials did provide them with access to LLM
    resources.


    The adversaries also used `GetModelInvocationLoggingConfiguration` to understand
    how the model was configured. This allowed them to see if prompt logging was enabled
    to help them avoid detection when executing prompts.'
  tactic: AML.TA0008
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: LLM Jacking
references:
- id: ref-1
  title: 'LLMjacking: Stolen Cloud Credentials Used in New AI Attack'
  url: https://sysdig.com/blog/llmjacking-stolen-cloud-credentials-used-in-new-ai-attack/
- id: ref-2
  title: 'The Growing Dangers of LLMjacking: Evolving Tactics and Evading Sanctions'
  url: https://sysdig.com/blog/growing-dangers-of-llmjacking/
- id: ref-3
  title: LLMjacking targets DeepSeek
  url: https://sysdig.com/blog/llmjacking-targets-deepseek/
- id: ref-4
  title: 'AIID Incident 898: Alleged LLMjacking Targets AI Cloud Services with Stolen
    Credentials'
  url: https://incidentdatabase.ai/cite/898
created-date: '2025-04-22'
modified-date: '2025-12-24'
type: Incident
actor: Unknown
target: Cloud-Based LLM Services
reporter: Sysdig Threat Research
date: '2024-05-06'
date-granularity: Day
id: AML.CS0030
uuid: 861228c8-adac-54d6-9fa9-cb6523848fac
object-type: case-study
```
