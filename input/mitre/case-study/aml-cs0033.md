---
title: Live Deepfake Image Injection to Evade Mobile KYC Verification
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-07'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0033
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0033
object_type: case-study
---

# AML.CS0033: Live Deepfake Image Injection to Evade Mobile KYC Verification

## Description

Facial biometric authentication services are commonly used by mobile applications for user onboarding, authentication, and identity verification for KYC requirements. The iProov Red Team demonstrated a face-swapped imagery injection attack that can successfully evade live facial recognition authentication models along with both passive and active [liveness verification](https://en.wikipedia.org/wiki/Liveness_test) on mobile devices. By executing this kind of attack, adversaries could gain access to privileged systems of a victim or create fake personas to create fake accounts on banking or cryptocurrency apps.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0033
  target: AML.T0015
  relationship-type: employs
  description: The researchers stream the deepfake video feed using OBS and use the
    Virtual Camera app to replace the default camera with feed. This successfully
    evades the facial recognition system and allows the researchers to authenticate
    themselves under the victim's identity.
  tactic: AML.TA0004
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0033
  target: AML.T0016
  relationship-type: employs
  description: 'The researchers obtained [Virtual Camera: Live Assist](https://apkpure.com/virtual-camera-live-assist/virtual.camera.app),
    an Android app that allows a user to substitute the devices camera  with a video
    stream. This app works on genuine, non-rooted Android devices.'
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0033
  target: AML.T0016.001
  relationship-type: employs
  description: The researchers obtained [Open Broadcaster Software (OBS)](https://obsproject.com)which
    can broadcast a video stream over the network.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0033
  target: AML.T0016.002
  relationship-type: employs
  description: The researchers obtained [Faceswap](https://swapface.org) a desktop
    application capable of swapping faces in a video in real-time.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0033
  target: AML.T0021
  relationship-type: employs
  description: The researchers used the gathered victim information to register an
    account for a financial services application.
  tactic: AML.TA0003
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0033
  target: AML.T0047
  relationship-type: employs
  description: During identity verification, the financial services application uses
    facial recognition and liveness detection to analyze live video from the user's
    camera.
  tactic: AML.TA0000
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0033
  target: AML.T0048.000
  relationship-type: employs
  description: The researchers could then have caused financial harm to the victim.
  tactic: AML.TA0011
  step-id: S09
  leads-to: []
- source: AML.CS0033
  target: AML.T0073
  relationship-type: employs
  description: With an authenticated account under the victim's identity, the researchers
    successfully impersonate the victim and evade detection.
  tactic: AML.TA0007
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0033
  target: AML.T0087
  relationship-type: employs
  description: The researchers collected user identity information and high-definition
    facial images from online social networks and/or black-market sites.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0033
  target: AML.T0088
  relationship-type: employs
  description: The researchers use the gathered victim face images and the Faceswap
    tool to produce live deepfake videos which mimic the victim's appearance.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: Live Deepfake Image Injection to Evade Mobile KYC Verification
references: []
created-date: '2025-11-07'
modified-date: '2025-11-07'
type: Exercise
actor: iProov Red Team
target: Mobile facial authentication service
date: '2024-10-01'
date-granularity: Year
id: AML.CS0033
uuid: 4e908d3f-94ee-5730-8757-ccf4f6f7173d
object-type: case-study
```
