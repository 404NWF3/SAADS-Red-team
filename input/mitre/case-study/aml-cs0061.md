---
title: 'AI in the Middle: Web-Based AI Services as C2 Relays'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-06-30'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0061
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0061
object_type: case-study
---

# AML.CS0061: AI in the Middle: Web-Based AI Services as C2 Relays

## Description

Check Point Research demonstrated an "AI in the Middle" attack in which malware can abuse web-based AI assistants with anonymous or unauthenticated browsing and URL-fetch capabilities as a covert command-and-control channel. The proof of concept used public AI web interfaces, including Grok and Microsoft Copilot, to cause the AI service to fetch attacker-controlled URLs, relay victim data in outbound requests, and return attacker-supplied commands through normal AI assistant responses.

Because the implant communicated with trusted AI service domains over ordinary HTTPS web traffic, the activity could blend into expected enterprise AI usage and evade controls focused on suspicious infrastructure, unusual protocols, API keys, service accounts, or revocable credentials. The lack of required authentication for some web-fetch workflows also made it harder for defenders to disable the channel by rotating API keys, suspending accounts, or revoking tokens. The researchers recommended stronger authentication and access controls for AI web-fetch features, along with improved visibility into AI-initiated network requests and AI assistant interactions.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0061
  target: AML.T0008.002
  relationship-type: employs
  description: The researchers registered a domain and deployed an HTTPS site to act
    as the relay endpoint.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0061
  target: AML.T0037
  relationship-type: employs
  description: The implant collected basic host information from the local system.
    The researchers noted that this could be expanded to collect details such as username,
    domain, computer name, installed software, running processes, and startup programs.
  tactic: AML.TA0009
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0061
  target: AML.T0047
  relationship-type: employs
  description: Assuming prior access, the researchers used a custom C++ implant with
    an embedded browser or WebView component to interact with Grok or Microsoft Copilot
    through the public web interface rather than an API key.
  tactic: AML.TA0000
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0061
  target: AML.T0050
  relationship-type: employs
  description: The AI service summarized the response from the adversary-controlled
    site, and the implant executed the extracted commands. In the proof of concept,
    the command launched Calculator using `cmd.exe /c calc.exe`; a real implant could
    execute other commands, download payloads, sleep, or collect additional data.
  tactic: AML.TA0005
  step-id: S09
  leads-to: []
- source: AML.CS0061
  target: AML.T0065
  relationship-type: employs
  description: The researchers crafted prompts that instruct an AI service to fetch
    and summarize a website. The prompts caused victim data to be included in URL
    parameters, allowing the AI service's fetch request to relay data to the adversary-controlled
    server.
  tactic: AML.TA0003
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0061
  target: AML.T0068
  relationship-type: employs
  description: When some prompts were blocked by model safeguards, the researchers
    encoded or encrypted payload data into high-entropy blobs to reduce the chance
    that safeguards would identify the content as malicious.
  tactic: AML.TA0007
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0061
  target: AML.T0079
  relationship-type: employs
  description: The researchers hosted benign-looking content while also returning
    data that the implant could treat as C2 instructions.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0061
  target: AML.T0086
  relationship-type: employs
  description: The victim's collected host information was exfiltrated when the AI
    service followed the instructions to fetch the URL to the adversary-controlled
    domain with the data embedded in a query parameter.
  tactic: AML.TA0010
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0061
  target: AML.T0095
  relationship-type: employs
  description: The researchers evaluated public AI assistants with anonymous or unauthenticated
    web-browsing and URL-fetch behavior to identify services that could retrieve arbitrary
    adversary-controlled URLs without requiring API credentials. The researchers found
    Grok and Copilot met those conditions.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0061
  target: AML.T0114
  relationship-type: employs
  description: The implant initiated an anonymous web-based session with the public
    AI service and sent the crafted prompt. This formed a command-and-control channel
    whereby data was exfiltrated via requests to the adversary-controlled domain,
    and commands were communicated back via the response.
  tactic: AML.TA0014
  step-id: S07
  leads-to:
  - S08
```

## Structured source fields

```yaml
name: 'AI in the Middle: Web-Based AI Services as C2 Relays'
references:
- id: checkpoint-ai-in-the-middle
  title: 'AI in the Middle: Turning Web-Based AI Services into C2 Proxies & The Future
    Of AI Driven Attacks'
  url: https://research.checkpoint.com/2026/ai-in-the-middle-turning-web-based-ai-services-into-c2-proxies-the-future-of-ai-driven-attacks/
created-date: '2026-06-30'
modified-date: '2026-06-30'
type: Exercise
actor: Check Point Research
target: Enterprise machines with Grok and Microsoft Copilot access
date: '2026-02-17'
date-granularity: Day
id: AML.CS0061
uuid: 5f159acc-41bb-5010-9b86-818b4f43a1ac
object-type: case-study
```
