---
title: Bypassing ID.me Identity Verification
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0017
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0017
object_type: case-study
---

# AML.CS0017: Bypassing ID.me Identity Verification

## Description

An individual filed at least 180 false unemployment claims in the state of California from October 2020 to December 2021 by bypassing ID.me's automated identity verification system. Dozens of fraudulent claims were approved and the individual received at least $3.4 million in payments.

The individual collected several real identities and obtained fake driver licenses using the stolen personal details and photos of himself wearing wigs. Next, he created accounts on ID.me and went through their identity verification process. The process validates personal details and verifies the user is who they claim by matching a photo of an ID to a selfie. The individual was able to verify stolen identities by wearing the same wig in his submitted selfie.

The individual then filed fraudulent unemployment claims with the California Employment Development Department (EDD) under the ID.me verified identities.
  Due to flaws in ID.me's identity verification process at the time, the forged
licenses were accepted by the system. Once approved, the individual had payments sent to various addresses he could access and withdrew the money via ATMs.
The individual was able to withdraw at least $3.4 million in unemployment benefits. EDD and ID.me eventually identified the fraudulent activity and reported it to federal authorities.  In May 2023, the individual was sentenced to 6 years and 9 months in prison for wire fraud and aggravated identify theft in relation to this and another fraud case.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0017
  target: AML.T0015
  relationship-type: employs
  description: 'The individual collected stolen identities, including names, dates
    of birth, and Social Security numbers. and used them along with a photo of himself
    wearing wigs to acquire fake driver''s licenses.


    The individual uploaded forged IDs along with a selfie. The ID.me document verification
    system matched the selfie to the ID photo, allowing some fraudulent claims to
    proceed in the application pipeline.'
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0017
  target: AML.T0047
  relationship-type: employs
  description: 'The individual applied for unemployment assistance with the California
    Employment Development Department using forged identities, interacting with ID.me''s
    identity verification system in the process.


    The system extracts content from a photo of an ID, validates the authenticity
    of the ID using a combination of AI and proprietary methods, then performs facial
    recognition to match the ID photo to a selfie. <sup>[[7]](https://network.id.me/wp-content/uploads/Document-Verification-Use-Machine-Vision-and-AI-to-Extract-Content-and-Verify-the-Authenticity-1.pdf)</sup>


    The individual identified that the California Employment Development Department
    relied on a third party service, ID.me, to verify individuals'' identities.


    The ID.me website outlines the steps to verify an identity, including entering
    personal information, uploading a driver license, and submitting a selfie photo.'
  tactic: AML.TA0000
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0017
  target: AML.T0048.000
  relationship-type: employs
  description: Dozens out of at least 180 fraudulent claims were ultimately approved
    and the individual received at least $3.4 million in unemployment assistance.
  tactic: AML.TA0011
  step-id: S02
  leads-to: []
```

## Structured source fields

```yaml
name: Bypassing ID.me Identity Verification
references:
- id: ref-1
  title: New Jersey Man Indicted in Fraud Scheme to Steal California Unemployment
    Insurance Benefits
  url: https://www.justice.gov/usao-edca/pr/new-jersey-man-indicted-fraud-scheme-steal-california-unemployment-insurance-benefits
- id: ref-2
  title: The Many Jobs and Wigs of Eric Jaklitchs Fraud Scheme
  url: https://frankonfraud.com/fraud-trends/the-many-jobs-and-wigs-of-eric-jaklitchs-fraud-scheme/
- id: ref-3
  title: ID.me gathers lots of data besides face scans, including locations. Scammers
    still have found a way around it.
  url: https://www.washingtonpost.com/technology/2022/02/11/idme-facial-recognition-fraud-scams-irs/
- id: ref-4
  title: CA EDD Unemployment Insurance & ID.me
  url: https://help.id.me/hc/en-us/articles/4416268603415-CA-EDD-Unemployment-Insurance-ID-me
- id: ref-5
  title: California EDD - How do I verify my identity for California EDD Unemployment
    Insurance?
  url: https://help.id.me/hc/en-us/articles/360054836774-California-EDD-How-do-I-verify-my-identity-for-the-California-Employment-Development-Department-
- id: ref-6
  title: New Jersey Man Sentenced to 6.75 Years in Prison for Schemes to Steal California
    Unemployment Insurance Benefits and Economic Injury Disaster Loans
  url: https://www.justice.gov/usao-edca/pr/new-jersey-man-sentenced-675-years-prison-schemes-steal-california-unemployment
- id: ref-7
  title: How ID.me uses machine vision and AI to extract content and verify the authenticity
    of ID documents
  url: https://network.id.me/wp-content/uploads/Document-Verification-Use-Machine-Vision-and-AI-to-Extract-Content-and-Verify-the-Authenticity-1.pdf
created-date: '2023-10-30'
modified-date: '2025-03-14'
type: Incident
actor: One individual
target: California Employment Development Department
reporter: ID.me internal investigation
date: '2020-10-01'
date-granularity: Month
id: AML.CS0017
uuid: 98798b51-207e-5e55-b1f3-e4dd43fc49e4
object-type: case-study
```
