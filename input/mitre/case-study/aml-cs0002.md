---
title: VirusTotal Poisoning
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0002
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0002
object_type: case-study
---

# AML.CS0002: VirusTotal Poisoning

## Description

McAfee Advanced Threat Research noticed an increase in reports of a certain ransomware family that was out of the ordinary. Case investigation revealed that many samples of that particular ransomware family were submitted through a popular virus-sharing platform within a short amount of time. Further investigation revealed that based on string similarity the samples were all equivalent, and based on code similarity they were between 98 and 74 percent similar. Interestingly enough, the compile time was the same for all the samples. After more digging, researchers discovered that someone used 'metame' a metamorphic code manipulating tool to manipulate the original file towards mutant variants. The variants would not always be executable, but are still classified as the same ransomware family.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0002
  target: AML.T0010.002
  relationship-type: employs
  description: The actor uploaded "mutant" samples to the platform.
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0002
  target: AML.T0016.000
  relationship-type: employs
  description: The actor obtained [metame](https://github.com/a0rtega/metame), a simple
    metamorphic code engine for arbitrary executables.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0002
  target: AML.T0020
  relationship-type: employs
  description: 'Several vendors started to classify the files as the ransomware family
    even though most of them won''t run.

    The "mutant" samples poisoned the dataset the ML model(s) use to identify and
    classify this ransomware family.'
  tactic: AML.TA0006
  step-id: S03
  leads-to: []
- source: AML.CS0002
  target: AML.T0043
  relationship-type: employs
  description: The actor used a malware sample from a prevalent ransomware family
    as a start to create "mutant" variants.
  tactic: AML.TA0001
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: VirusTotal Poisoning
references: []
created-date: '2020-12-03'
modified-date: '2025-03-14'
type: Incident
actor: Unknown
target: VirusTotal
reporter: McAfee Advanced Threat Research
date: '2020-01-01'
date-granularity: Year
id: AML.CS0002
uuid: 88bc2bb6-e36e-5786-be9a-90b67a096adb
object-type: case-study
```
