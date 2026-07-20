---
title: 'ProKYC: Deepfake Tool for Account Fraud Attacks'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-07'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0034
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0034
object_type: case-study
---

# AML.CS0034: ProKYC: Deepfake Tool for Account Fraud Attacks

## Description

Cato CTRL security researchers have identified ProKYC, a deepfake tool being sold to cybercriminals as a method to bypass Know Your Customer (KYC) verification on financial service applications such as cryptocurrency exchanges. ProKYC can create fake identity documents and generate deepfake selfie videos, two key pieces of biometric data used during KYC verification. The tool helps cybercriminals defeat facial recognition and liveness checks to create fraudulent accounts.

The procedure below describes how a bad actor could use ProKYC's service to bypass KYC verification.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0034
  target: AML.T0015
  relationship-type: employs
  description: The bad actor used ProKYC to replace the camera feed with the deepfake
    selfie video. This successfully evaded the KYC verification and allowed the bad
    actor to authenticate themselves under the false identity.
  tactic: AML.TA0004
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0034
  target: AML.T0016.002
  relationship-type: employs
  description: The bad actor paid for the ProKYC tool, created a fake identity document,
    generated a deepfake selfie video, and replaced a live camera feed with the deepfake
    video.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0034
  target: AML.T0021
  relationship-type: employs
  description: The bad actor used the victim information to register an account with
    a financial services application, such as a cryptocurrency exchange.
  tactic: AML.TA0003
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0034
  target: AML.T0047
  relationship-type: employs
  description: During identity verification, the financial services application used
    facial recognition and liveness detection to analyze live video from the user's
    camera.
  tactic: AML.TA0000
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0034
  target: AML.T0048.000
  relationship-type: employs
  description: The bad actor used this access to cause financial harm to the victim.
  tactic: AML.TA0011
  step-id: S08
  leads-to: []
- source: AML.CS0034
  target: AML.T0073
  relationship-type: employs
  description: With an authenticated account under the victim's identity, the bad
    actor successfully impersonated the victim and evaded detection.
  tactic: AML.TA0007
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0034
  target: AML.T0087
  relationship-type: employs
  description: The bad actor collected user identity information.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0034
  target: AML.T0088
  relationship-type: employs
  description: The bad actor used a mixture of real PII and falsified details with
    the ProKYC tool to generate a deepfaked identity document.
  tactic: AML.TA0001
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0034
  target: AML.T0088
  relationship-type: employs
  description: The bad actor used ProKYC tool to generate a deepfake selfie video
    with the same face as the identity document designed to bypass liveness checks.
  tactic: AML.TA0001
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: 'ProKYC: Deepfake Tool for Account Fraud Attacks'
references:
- id: ref-1
  title: 'AIID Incident 819: ProKYC Tool Allegedly Facilitates Deepfake-Based Account
    Fraud on Cryptocurrency Exchanges'
  url: https://incidentdatabase.ai/cite/819/
- id: ref-2
  title: 'Cato CTRL Threat Research: ProKYC - Deepfake Tool for Account Fraud Attacks'
  url: https://www.catonetworks.com/blog/prokyc-selling-deepfake-tool-for-account-fraud-attacks/
- id: ref-3
  title: 'ProKYC: Synthetic Identity Fraud as a Service'
  url: https://idscan.net/blog/prokyc-synthetic-identity-fraud/
created-date: '2025-11-07'
modified-date: '2025-11-07'
type: Incident
actor: ProKYC, cybercriminal group
target: KYC verification services
reporter: Cato CTRL
date: '2024-10-09'
date-granularity: Day
id: AML.CS0034
uuid: 05540757-88ce-5dab-8b18-31e75e5dbfed
object-type: case-study
```
