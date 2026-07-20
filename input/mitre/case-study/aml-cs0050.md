---
title: OpenClaw 1-Click Remote Code Execution
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-02-06'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0050
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0050
object_type: case-study
---

# AML.CS0050: OpenClaw 1-Click Remote Code Execution

## Description

A security researcher demonstrated a 1-click remote code execution (RCE) vulnerability to the OpenClaw AI Agent via a malicious link containing a JavaScript script that only takes milliseconds to execute. This vulnerability has been reported and is being tracked to versions of OpenClaw as CVE-2026-25253. [[nvd]]  OpenClaw "is a personal AI assistant you run on your own devices. It answers you on the chat apps you already use. Unlike SaaS assistants where your data lives on someone else's servers, OpenClaw runs where you choose - laptop, homelab, or VPS. Your infrastructure. Your keys. Your data." [[openclaw]]

The researcher demonstrated that when the victim clicks a malicious link, a client-side JavaScript script is executed on the victim's browser that can steal authentication tokens from the OpenClaw control interface via a WebSocket connection. It then uses Cross-Site WebSocket Hijacking to bypass localhost restrictions to the OpenClaw Gateway API.  Once the connection was established, it uses the stolen token to authenticate and modify the OpenClaw agent configuration to disable user confirmation and escape the container, allowing shell commands to be run directly on the host machine.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0050
  target: AML.T0011.003
  relationship-type: employs
  description: When the victim clicked the link to the researchers' website, the malicious
    JavaScript script executes in the user's browser.
  tactic: AML.TA0005
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0050
  target: AML.T0012
  relationship-type: employs
  description: The malicious script used the stolen Gateway token to authenticate,
    allowing subsequent calls to OpenClaw's Gateway API on the victim's system.
  tactic: AML.TA0012
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0050
  target: AML.T0017
  relationship-type: employs
  description: The researcher developed a 1-Click RCE JavaScript script.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0050
  target: AML.T0050
  relationship-type: employs
  description: The malicious script achieved remote code execution by sending a `node.invoke`
    (OpenClaw's RPC mechanism) request to OpenClaw's API.
  tactic: AML.TA0005
  step-id: S08
  leads-to: []
- source: AML.CS0050
  target: AML.T0079
  relationship-type: employs
  description: The researcher staged the malicious script at an inconspicuous website.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0050
  target: AML.T0081
  relationship-type: employs
  description: "The malicious script disabled OpenClaw's security feature that prompts\
    \ users before running potentially dangerous commands. This was done by sending\
    \ the following payload to OpenClaw's Gateway API:\n```\n{ \"method\": \"exec.approvals.set\"\
    ,\n  \"params\": { \"defaults\": { \"security\": \"full\", \"ask\": \"off\" }\
    \ }\n}\n```"
  tactic: AML.TA0007
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0050
  target: AML.T0105
  relationship-type: employs
  description: The malicious script disabled OpenClaw's sandboxing, forcing the agent
    to run commands directly on the host machine instead of inside a docker container.
    This was done by sending a `config.patch` request to OpenClaw's Gateway API to
    set `tools.exec.host` to "gateway".
  tactic: AML.TA0012
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0050
  target: AML.T0106
  relationship-type: employs
  description: The malicious script opened a background window to the victim's OpenClaw
    control interface with the `gatewayUrl` set to a WebSocket address on the researcher's
    server. OpenClaw's control interface trusts the `gatewayUrl` query string without
    validation and auto-connects on load, sending the Gateway token to the researcher's
    server.
  tactic: AML.TA0013
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0050
  target: AML.T0107
  relationship-type: employs
  description: The malicious script performed Cross-Site WebSocket Hijacking (CSWSH)
    to bypass localhost network restrictions. It opened a new WebSocket connection
    to the OpenClaw Gateway server on localhost.
  tactic: AML.TA0007
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: OpenClaw 1-Click Remote Code Execution
references:
- id: depthfirst
  title: 1-Click RCE To Steal Your Moltbot Data and Keys (CVE-2026-25253)
  url: https://depthfirst.com/post/1-click-rce-to-steal-your-moltbot-data-and-keys
- id: nvd
  title: CVE-2026-25253
  url: https://nvd.nist.gov/vuln/detail/CVE-2026-25253
- id: openclaw
  title: openclaw
  url: https://openclaw.ai/blog/introducing-openclaw
created-date: '2026-02-06'
modified-date: '2026-02-06'
type: Exercise
actor: DepthFirst
target: OpenClaw
date: '2026-02-01'
date-granularity: Day
id: AML.CS0050
uuid: 2e088741-9d94-550b-a667-e46e33e31738
object-type: case-study
```
