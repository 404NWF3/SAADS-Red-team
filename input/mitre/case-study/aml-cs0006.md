---
title: ClearviewAI Misconfiguration
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0006
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0006
object_type: case-study
---

# AML.CS0006: ClearviewAI Misconfiguration

## Description

Clearview AI makes a facial recognition tool that searches publicly available photos for matches.  This tool has been used for investigative purposes by law enforcement agencies and other parties.

Clearview AI's source code repository, though password protected, was misconfigured to allow an arbitrary user to register an account.
This allowed an external researcher to gain access to a private code repository that contained Clearview AI production credentials, keys to cloud storage buckets containing 70K video samples, and copies of its applications and Slack tokens.
With access to training data, a bad actor has the ability to cause an arbitrary misclassification in the deployed model.
These kinds of attacks illustrate that any attempt to secure ML system should be on top of "traditional" good cybersecurity hygiene such as locking down the system with least privileges, multi-factor authentication and monitoring and auditing.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0006
  target: AML.T0002
  relationship-type: employs
  description: Adversaries could have downloaded training data and gleaned details
    about software, models, and capabilities from the source code and decompiled application
    binaries.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0006
  target: AML.T0021
  relationship-type: employs
  description: A security researcher gained initial access to Clearview AI's private
    code repository via a misconfigured server setting that allowed an arbitrary user
    to register a valid account.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0006
  target: AML.T0031
  relationship-type: employs
  description: As a result, future application releases could have been compromised,
    causing degraded or malicious facial recognition capabilities.
  tactic: AML.TA0011
  step-id: S03
  leads-to: []
- source: AML.CS0006
  target: AML.T0036
  relationship-type: employs
  description: 'The private code repository contained credentials which were used
    to access AWS S3 cloud storage buckets, leading to the discovery of assets for
    the facial recognition tool, including:

    - Released desktop and mobile applications

    - Pre-release applications featuring new capabilities

    - Slack access tokens

    - Raw videos and other data'
  tactic: AML.TA0009
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: ClearviewAI Misconfiguration
references:
- id: ref-1
  title: TechCrunch Article, "Security lapse exposed Clearview AI source code"
  url: https://techcrunch.com/2020/04/16/clearview-source-code-lapse/
- id: ref-2
  title: Gizmodo Article, "We Found Clearview AI's Shady Face Recognition App"
  url: https://gizmodo.com/we-found-clearview-ais-shady-face-recognition-app-1841961772
- id: ref-3
  title: New York Times Article, "The Secretive Company That Might End Privacy as
    We Know It"
  url: https://www.nytimes.com/2020/01/18/technology/clearview-privacy-facial-recognition.html
created-date: '2020-10-23'
modified-date: '2025-03-14'
type: Incident
actor: Researchers at spiderSilk
target: Clearview AI facial recognition tool
date: '2020-04-16'
date-granularity: Month
id: AML.CS0006
uuid: 47c987d3-c19a-5120-91ab-2752ad8a0788
object-type: case-study
```
