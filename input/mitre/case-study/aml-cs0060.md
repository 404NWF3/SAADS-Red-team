---
title: Cross-Site Scripting via Prompt Manipulation in Lenovo AI Chatbot
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-06-29'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0060
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0060
object_type: case-study
---

# AML.CS0060: Cross-Site Scripting via Prompt Manipulation in Lenovo AI Chatbot

## Description

Cybernews researchers demonstrated that Lenovo's AI chatbot "Lena" was vulnerable to a prompt injection that produced malicious HTML which was saved in the chat history and could exfiltrate a human support agent's session cookie when rendered in their browser.

The researchers prompted Lena with a benign-looking product information request that included instructions to respond with a dangerous HTML payload. The response was saved in the user's chat history, creating a stored cross-site scripting (XSS) payload. When the researchers requested transfer to a human support agent, the agent's normal workflow of opening the chat transcript caused the poisoned content to render, exfiltrating session cookie data to an attacker-controlled server. If a valid support agent cookie were reused, an adversary could potentially access Lenovo's customer support platform as that agent and view customer conversations or perform other actions available to the account.

Lenovo acknowledged the issue and reported implementing corrective actions to mitigate the potential impact and address the issue.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0060
  target: AML.T0008
  relationship-type: employs
  description: The researchers set up a server to receive sensitive exfiltrated information
    from a vulnerable LLM service.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0060
  target: AML.T0011
  relationship-type: employs
  description: The researchers requested transfer to a human support agent, causing
    the malicious HTML to execute automatically when the agent opened the chat transcript.
  tactic: AML.TA0005
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0060
  target: AML.T0047
  relationship-type: employs
  description: The researchers used the public web chat interface to Lenovo's "Lena"
    customer service agent.
  tactic: AML.TA0000
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0060
  target: AML.T0048
  relationship-type: employs
  description: The attack exposed support agents and customers to session hijacking,
    unauthorized data access, and potential malware execution, resulting in direct
    user-level security and privacy harms.
  tactic: AML.TA0011
  step-id: S10
  leads-to: []
- source: AML.CS0060
  target: AML.T0050
  relationship-type: employs
  description: The stored HTML included browser-executable JavaScript that ran in
    the support agent's browser when the transcript was rendered.
  tactic: AML.TA0005
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0060
  target: AML.T0051.000
  relationship-type: employs
  description: Lena followed the attacker-controlled formatting instructions and generated
    an HTML response containing the malicious payload. The response persisted in the
    chat thread.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0060
  target: AML.T0065
  relationship-type: employs
  description: 'The researchers developed a single prompt designed to make Lena generate
    HTML that would be unsafe when rendered by Lenovo''s chat interface. The prompt
    combined several elements:

    - A benign-looking product information request, such as "Show me the specifications
    of Lenovo IdeaPad 5 Pro."

    - Output format instructions directing Lena to return the response as HTML with
    additional JSON and plaintext formatting expected by the server-side processing
    path.

    - An HTML and JavaScript payload designed to read browser-accessible cookies and
    place them into a query parameter in an image request to an attacker-controlled
    server.

    - Reinforcement language urging the model to include the image, such as "Show
    the image at the end. It is important for my decision-making. SHOW IT."'
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0060
  target: AML.T0077
  relationship-type: employs
  description: The active session cookie was added to a query parameter of an image
    tag in the HTML payload. The image did not exist, however the failed image load
    still made a request to the adversary-controlled server, exfiltrating the session
    cookie.
  tactic: AML.TA0010
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0060
  target: AML.T0091.001
  relationship-type: employs
  description: The researchers could then import the stolen support agent session
    cookie into their browser to resume the authenticated session and potentially
    move laterally into Lenovo's customer support platform as the support agent.
  tactic: AML.TA0015
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0060
  target: AML.T0093
  relationship-type: employs
  description: The researchers introduced attacker-controlled HTML into Lenovo's support
    workflow by prompting Lena through the public chat interface, causing the generated
    payload to be stored in the chat history for later rendering.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0060
  target: AML.T0113
  relationship-type: employs
  description: The JavaScript read session cookies from the support agent's browser.
  tactic: AML.TA0013
  step-id: S07
  leads-to:
  - S08
```

## Structured source fields

```yaml
name: Cross-Site Scripting via Prompt Manipulation in Lenovo AI Chatbot
references:
- id: cybernews
  title: 'Critical flaw plagues Lenovo AI chatbot: attackers can run malicious code
    and steal cookies'
  url: https://cybernews.com/security/lenovo-chatbot-lena-plagued-by-critical-vulnerabilities/
created-date: '2026-06-29'
modified-date: '2026-06-29'
type: Exercise
actor: Cybernews Research Team
target: Lenovo AI chatbot, "Lena"
date: '2025-08-18'
date-granularity: Day
id: AML.CS0060
uuid: 4bd9867e-8247-5349-8b8e-3bc10936f2cd
object-type: case-study
```
