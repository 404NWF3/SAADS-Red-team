---
title: AI Model Tampering via Supply Chain Attack
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-08-12'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0028
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0028
object_type: case-study
---

# AML.CS0028: AI Model Tampering via Supply Chain Attack

## Description

Researchers at Trend Micro, Inc. used service indexing portals and web searching tools to identify over 8,000 misconfigured private container registries exposed on the internet. Approximately 70% of the registries also had overly permissive access controls that allowed write access. In their analysis, the researchers found over 1,000 unique AI models embedded in private container images within these open registries that could be pulled without authentication.

This exposure could allow adversaries to download, inspect, and modify container contents, including sensitive AI model files. This is an exposure of valuable intellectual property which could be stolen by an adversary. Compromised images could also be pushed to the registry, leading to a supply chain attack, allowing malicious actors to compromise the integrity of AI models used in production systems.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0028
  target: AML.T0004
  relationship-type: employs
  description: 'The Trend Micro researchers used service indexing portals and web
    searching tools to identify over 8,000 private container registries exposed on
    the internet. Approximately 70% of the registries had overly permissive access
    controls, allowing write permissions. The private container registries encompassed
    both independently hosted registries and registries deployed on Cloud Service
    Providers (CSPs). The registries were exposed due to some combination of:


    - Misconfiguration leading to public access of private registry,

    - Lack of proper authentication and authorization mechanisms, and/or

    - Insufficient network segmentation and access controls'
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0028
  target: AML.T0007
  relationship-type: employs
  description: The researchers found 1,453 unique AI models embedded in the private
    container images. Around half were in the Open Neural Network Exchange (ONNX)
    format.
  tactic: AML.TA0008
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0028
  target: AML.T0010.004
  relationship-type: employs
  description: Because many of the misconfigured container registries allowed write
    access, the adversary's container image with the manipulated model could be pushed
    with the same name and tag as the original. This compromises the victim's AI supply
    chain, where automated CI/CD pipelines could pull the adversary's images.
  tactic: AML.TA0004
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0028
  target: AML.T0015
  relationship-type: employs
  description: Once the adversary's container image is deployed, the model may misclassify
    inputs due to the adversary's manipulations.
  tactic: AML.TA0011
  step-id: S08
  leads-to: []
- source: AML.CS0028
  target: AML.T0018.000
  relationship-type: employs
  description: With full access to the model weights, an adversary could manipulate
    the weights to cause misclassifications or otherwise degrade performance.
  tactic: AML.TA0006
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0028
  target: AML.T0018.001
  relationship-type: employs
  description: With full access to the model, an adversary could modify the architecture
    to change the behavior.
  tactic: AML.TA0006
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0028
  target: AML.T0044
  relationship-type: employs
  description: 'This gave the researchers full access to the models. Models for a
    variety of use cases were identified, including:


    - ID Recognition

    - Face Recognition

    - Object Recognition

    - Various Natural Language Processing Tasks'
  tactic: AML.TA0000
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0028
  target: AML.T0048.004
  relationship-type: employs
  description: With full access to the model(s), an adversary has an organization's
    valuable intellectual property.
  tactic: AML.TA0011
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0028
  target: AML.T0049
  relationship-type: employs
  description: The researchers were able to exploit the misconfigured registries to
    pull container images without requiring authentication. In total, researchers
    pulled several terabytes of data containing over 20,000 images.
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: AI Model Tampering via Supply Chain Attack
references:
- id: ref-1
  title: 'Silent Sabotage: Weaponizing AI Models in Exposed Containers'
  url: https://www.trendmicro.com/vinfo/br/security/news/cyber-attacks/silent-sabotage-weaponizing-ai-models-in-exposed-containers
- id: ref-2
  title: 'Exposed Container Registries: A Potential Vector for Supply-Chain Attacks'
  url: https://www.trendmicro.com/vinfo/us/security/news/virtualization-and-cloud/exposed-container-registries-a-potential-vector-for-supply-chain-attacks
- id: ref-3
  title: 'Mining Through Mountains of Information and Risk: Containers and Exposed
    Container Registries'
  url: https://www.trendmicro.com/vinfo/us/security/news/virtualization-and-cloud/mining-through-mountains-of-information-and-risk-containers-and-exposed-container-registries
- id: ref-4
  title: 'The Growing Threat of Unprotected Container Registries: An Urgent Call to
    Action'
  url: https://www.dreher.in/blog/unprotected-container-registries
created-date: '2025-04-22'
modified-date: '2025-08-12'
type: Exercise
actor: Trend Micro Nebula Cloud Research Team
target: Private Container Registries
date: '2023-09-26'
date-granularity: Day
id: AML.CS0028
uuid: 2e19d9f8-1deb-5323-befc-0b53ff64ceb8
object-type: case-study
```
