---
title: 'AIKatz: Attacking LLM Desktop Applications'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-26'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0036
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0036
object_type: case-study
---

# AML.CS0036: AIKatz: Attacking LLM Desktop Applications

## Description

Researchers at Lumia have demonstrated that it is possible to extract authentication tokens from the memory of LLM Desktop Applications. An attacker could then use those tokens to impersonate as the victim to the LLM backed, thereby gaining access to the victim's conversations as well as the ability to interfere in future conversations. The attacker's access would allow them the ability to directly inject prompts to change the LLM's behavior, poison the LLM's context to have persistent effects, manipulate the user's conversation history to cover their tracks, and ultimately impact the confidentiality, integrity, and availability of the system. The researchers demonstrated this on Anthropic Claude, Microsoft M365 Copilot, and OpenAI ChatGPT.

Vendor Responses to Responsible Disclosure:
- Anthropic (HackerOne) - Closed as informational since local attack.
- Microsoft Security Response Center - Attack doesn't bypass security boundaries for CVE.
- OpenAI (BugCrowd) - Closed as informational and noted that it's up to Microsoft to patch this behavior.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0036
  target: AML.T0012
  relationship-type: employs
  description: The attacker required initial access to the victim system to carry
    out this attack.
  tactic: AML.TA0004
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0036
  target: AML.T0029
  relationship-type: employs
  description: The attacker could delete all chats the victim has, and any they are
    opening, thereby preventing the victim from being able to interact with the LLM.
  tactic: AML.TA0011
  step-id: S11
  leads-to:
  - S12
- source: AML.CS0036
  target: AML.T0029
  relationship-type: employs
  description: The attacker could spam messages or prompts to reach the LLM's rate-limits
    against bots, to cause it to ban the victim altogether.
  tactic: AML.TA0011
  step-id: S12
  leads-to: []
- source: AML.CS0036
  target: AML.T0047
  relationship-type: employs
  description: The attacker has now obtained the access required to communicate with
    the LLM backend service as if they were the desktop client. This allowed them
    access to everything the user can do with the desktop application.
  tactic: AML.TA0000
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0036
  target: AML.T0048.000
  relationship-type: employs
  description: The attacker could send spam messages while impersonating the victim.
    On a pay-per-token or action plans, this could increase the financial burden on
    the victim.
  tactic: AML.TA0011
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0036
  target: AML.T0048.003
  relationship-type: employs
  description: The attacker could gain access to all of the victim's activity with
    the LLM, including previous and ongoing chats, as well as any file or content
    uploaded to them.
  tactic: AML.TA0011
  step-id: S10
  leads-to:
  - S11
- source: AML.CS0036
  target: AML.T0051.000
  relationship-type: employs
  description: The attacker sent malicious prompts directly to the LLM under any ongoing
    conversation the victim has.
  tactic: AML.TA0005
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0036
  target: AML.T0080.000
  relationship-type: employs
  description: The attacker could then craft malicious prompts that manipulate the
    LLM's memory to achieve a persistent effect. Any change in memory would also propagate
    to any new chat threads.
  tactic: AML.TA0006
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0036
  target: AML.T0080.001
  relationship-type: employs
  description: The attacker could craft malicious prompts that manipulate the context
    of a chat thread, an effect that would persist for the duration of the thread.
  tactic: AML.TA0006
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0036
  target: AML.T0089
  relationship-type: employs
  description: The attacker enumerated all of the processes running on the victim's
    machine and identified the processes belonging to LLM desktop applications.
  tactic: AML.TA0008
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0036
  target: AML.T0090
  relationship-type: employs
  description: The attacker attached or read memory directly from `/proc` (in Linux)
    or opened a handle to the LLM application's process (in Windows). The attacker
    then scanned the process's memory to extract the authentication token of the victim.
    This can be easily done by running a regex on every allocated memory page in the
    process.
  tactic: AML.TA0013
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0036
  target: AML.T0091.000
  relationship-type: employs
  description: The attacker used the extracted token to authenticate themselves with
    the LLM backend service.
  tactic: AML.TA0015
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0036
  target: AML.T0092
  relationship-type: employs
  description: Many LLM desktop applications do not show the injected prompt for any
    ongoing chat, as they update chat history only once when initially opening it.
    This gave the attacker the opportunity to cover their tracks by manipulating the
    user's conversation history directly via the LLM's API. The attacker could also
    overwrite or delete messages to prevent detection of their actions.
  tactic: AML.TA0007
  step-id: S08
  leads-to:
  - S09
```

## Structured source fields

```yaml
name: 'AIKatz: Attacking LLM Desktop Applications'
references:
- id: ref-1
  title: AIKatz - All Your Chats Are Belong To Us
  url: https://www.lumia.security/blog/aikatz
created-date: '2025-11-07'
modified-date: '2025-11-26'
type: Exercise
actor: Lumia Security
target: LLM Desktop Applications (Claude, ChatGPT, Copilot)
date: '2025-01-01'
date-granularity: Year
id: AML.CS0036
uuid: 9aabba83-3e0d-5265-930b-5e1e0408ed16
object-type: case-study
```
