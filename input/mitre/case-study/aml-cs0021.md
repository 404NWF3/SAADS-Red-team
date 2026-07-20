---
title: ChatGPT Conversation Exfiltration
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-04-22'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0021
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0021
object_type: case-study
---

# AML.CS0021: ChatGPT Conversation Exfiltration

## Description

[Embrace the Red](https://embracethered.com/blog/) demonstrated that ChatGPT users' conversations can be exfiltrated via an indirect prompt injection. To execute the attack, a threat actor uploads a malicious prompt to a public website, where a ChatGPT user may interact with it. The prompt causes ChatGPT to respond with the markdown for an image, whose URL has the user's conversation secretly embedded. ChatGPT renders the image for the user, creating a automatic request to an adversary-controlled script and exfiltrating the user's conversation. Additionally, the researcher demonstrated how the prompt can execute other plugins, opening them up to additional harms.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0021
  target: AML.T0048.003
  relationship-type: employs
  description: The user's privacy is violated, and they are potentially open to further
    targeted attacks.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0021
  target: AML.T0051.001
  relationship-type: employs
  description: The prompt injection is executed, causing ChatGPT to include a Markdown
    element for an image hosted on an adversary-controlled server and embed the user's
    chat history as query parameter in the URL.
  tactic: AML.TA0005
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0021
  target: AML.T0053
  relationship-type: employs
  description: Additionally, the prompt can cause the LLM to execute other plugins
    that do not match a user request. In this instance, the researcher demonstrated
    the `WebPilot` plugin making a call to the `Expedia` plugin.
  tactic: AML.TA0012
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0021
  target: AML.T0065
  relationship-type: employs
  description: The researcher developed a prompt that causes ChatGPT to include a
    Markdown element for an image with the user's conversation embedded in the URL
    as part of its responses.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0021
  target: AML.T0077
  relationship-type: employs
  description: ChatGPT automatically renders the image for the user, making the request
    to the adversary's server for the image contents, and exfiltrating the user's
    conversation.
  tactic: AML.TA0010
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0021
  target: AML.T0078
  relationship-type: employs
  description: When the user makes a query that causes ChatGPT to retrieve the webpage
    using its `WebPilot` plugin, it ingests the adversary's prompt.
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0021
  target: AML.T0079
  relationship-type: employs
  description: The researcher included the prompt in a webpage, where it could be
    retrieved by ChatGPT.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: ChatGPT Conversation Exfiltration
references:
- id: ref-1
  title: 'ChatGPT Plugins: Data Exfiltration via Images & Cross Plugin Request Forgery'
  url: https://embracethered.com/blog/posts/2023/chatgpt-webpilot-data-exfil-via-markdown-injection/
created-date: '2023-10-30'
modified-date: '2025-04-22'
type: Exercise
actor: Embrace The Red
target: OpenAI ChatGPT
date: '2023-05-01'
date-granularity: Month
id: AML.CS0021
uuid: 185a639b-c7ed-50ff-acd3-0c00ae3206ca
object-type: case-study
```
