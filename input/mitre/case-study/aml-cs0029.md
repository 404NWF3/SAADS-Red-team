---
title: Google Bard Conversation Exfiltration
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-07'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0029
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0029
object_type: case-study
---

# AML.CS0029: Google Bard Conversation Exfiltration

## Description

[Embrace the Red](https://embracethered.com/blog/) demonstrated that Bard users' conversations could be exfiltrated via an indirect prompt injection. To execute the attack, a threat actor shares a Google Doc containing the prompt with the target user who then interacts with the document via Bard to inadvertently execute the prompt. The prompt causes Bard to respond with the markdown for an image, whose URL has the user's conversation secretly embedded. Bard renders the image for the user, creating an automatic request to an adversary-controlled script and exfiltrating the user's conversation. The request is not blocked by Google's Content Security Policy (CSP), because the script is hosted as a Google Apps Script with a Google-owned domain.

Note: Google has fixed this vulnerability. The CSP remains the same, and Bard can still render images for the user, so there may be some filtering of data embedded in URLs.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0029
  target: AML.T0008
  relationship-type: employs
  description: The researcher identified that Google Apps Scripts can be invoked via
    a URL on `script.google.com` or `googleusercontent.com` and can be configured
    to not require authentication. This allows a script to be invoked without triggering
    Bard's Content Security Policy.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0029
  target: AML.T0017
  relationship-type: employs
  description: The researcher wrote a Google Apps Script that logs all query parameters
    to a Google Doc.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0029
  target: AML.T0048.003
  relationship-type: employs
  description: The user's conversation is exfiltrated, violating their privacy, and
    possibly enabling further targeted attacks.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0029
  target: AML.T0051.001
  relationship-type: employs
  description: When the user makes a query that results in the document being retrieved,
    the embedded prompt is executed. The malicious prompt causes Bard to respond with
    markdown for an image whose URL points to the researcher's Google App Script with
    the user's conversation in a query parameter.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0029
  target: AML.T0065
  relationship-type: employs
  description: The researcher developed a prompt that causes Bard to include a Markdown
    element for an image with the user's conversation embedded in the URL as part
    of its responses.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0029
  target: AML.T0077
  relationship-type: employs
  description: Bard automatically renders the markdown, which sends the request to
    the Google App Script, exfiltrating the user's conversation. This is allowed by
    Bard's Content Security Policy because the URL is hosted on a Google-owned domain.
  tactic: AML.TA0010
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0029
  target: AML.T0093
  relationship-type: employs
  description: The researcher shares a Google Doc containing the malicious prompt
    with the target user. This exploits the fact that Bard Extensions allow Bard to
    access a user's documents.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: Google Bard Conversation Exfiltration
references:
- id: ref-1
  title: Hacking Google Bard - From Prompt Injection to Data Exfiltration
  url: https://embracethered.com/blog/posts/2023/google-bard-data-exfiltration/
created-date: '2025-04-22'
modified-date: '2025-11-07'
type: Exercise
actor: Embrace the Red
target: Google Bard
date: '2023-11-23'
date-granularity: Day
id: AML.CS0029
uuid: 31136483-7dd8-58f5-9aee-ba24f867770e
object-type: case-study
```
