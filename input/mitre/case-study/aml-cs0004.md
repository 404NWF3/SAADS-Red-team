---
title: Camera Hijack Attack on Facial Recognition System
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0004
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0004
object_type: case-study
---

# AML.CS0004: Camera Hijack Attack on Facial Recognition System

## Description

This type of camera hijack attack can evade the traditional live facial recognition authentication model and enable access to privileged systems and victim impersonation.

Two individuals in China used this attack to gain access to the local government's tax system. They created a fake shell company and sent invoices via tax system to supposed clients. The individuals started this scheme in 2018 and were able to fraudulently collect $77 million.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0004
  target: AML.T0008.001
  relationship-type: employs
  description: The attackers bought customized low-end mobile phones.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0004
  target: AML.T0015
  relationship-type: employs
  description: The attackers successfully evaded the face recognition system. This
    allowed the attackers to impersonate the victim and verify their identity in the
    tax system.
  tactic: AML.TA0004
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0004
  target: AML.T0016.000
  relationship-type: employs
  description: The attackers obtained software that turns static photos into videos,
    adding realistic effects such as blinking eyes.
  tactic: AML.TA0003
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0004
  target: AML.T0016.001
  relationship-type: employs
  description: The attackers obtained customized Android ROMs and a virtual camera
    application.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0004
  target: AML.T0021
  relationship-type: employs
  description: The attackers used the victim identity information to register new
    accounts in the tax system.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0004
  target: AML.T0047
  relationship-type: employs
  description: The attackers used the virtual camera app to present the generated
    video to the ML-based facial recognition service used for user verification.
  tactic: AML.TA0000
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0004
  target: AML.T0048.000
  relationship-type: employs
  description: The attackers used their privileged access to the tax system to send
    invoices to supposed clients and further their fraud scheme.
  tactic: AML.TA0011
  step-id: S07
  leads-to: []
- source: AML.CS0004
  target: AML.T0087
  relationship-type: employs
  description: The attackers collected user identity information and high-definition
    face photos from an online black market.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
```

## Structured source fields

```yaml
name: Camera Hijack Attack on Facial Recognition System
references:
- id: ref-1
  title: Faces are the next target for fraudsters
  url: https://www.wsj.com/articles/faces-are-the-next-target-for-fraudsters-11625662828
created-date: '2020-12-03'
modified-date: '2026-03-31'
type: Incident
actor: Two individuals
target: Shanghai government tax office's facial recognition service
reporter: Ant Group AISEC Team
date: '2020-01-01'
date-granularity: Year
id: AML.CS0004
uuid: 807233cc-a867-588a-8455-22df4fa0ae65
object-type: case-study
```
