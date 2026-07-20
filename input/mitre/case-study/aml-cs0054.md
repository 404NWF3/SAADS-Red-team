---
title: Data Exfiltration via Remote Poisoned MCP Tool
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0054
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0054
object_type: case-study
---

# AML.CS0054: Data Exfiltration via Remote Poisoned MCP Tool

## Description

Researchers at Invariant Labs demonstrated that AI agents configured with remote Model Context Protocol (MCP) Tools can be vulnerable to model poisoning attacks. They show that an MCP Tool can contain malicious prompts in its docstring description, which is ingested into the AI agent's context, modifying its behavior.

They demonstrate this attack with a proof-of-concept MCP Tool that instructs the agent to perform additional actions before using the tool. The agent is instructed to read files containing credentials from the victim's machine and store their contents in one of the input variables to the tool. When the tool runs, the victim's credentials are exfiltrated to the poisoned MCP server.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0054
  target: AML.T0010.005
  relationship-type: employs
  description: The researchers hosted a poisoned MCP tool that contains the malicious
    instructions hidden in the docstring of the tool.
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0054
  target: AML.T0048.003
  relationship-type: employs
  description: The user's private data was exposed to remote MCP server.
  tactic: AML.TA0011
  step-id: S08
  leads-to: []
- source: AML.CS0054
  target: AML.T0051.000
  relationship-type: employs
  description: When a user called the remote MCP tool, the prompt injection hidden
    in the docstring is executed locally.
  tactic: AML.TA0005
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0054
  target: AML.T0053
  relationship-type: employs
  description: The prompt invoked an agent tool capable of reading files from the
    victim's filesystem.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0054
  target: AML.T0055
  relationship-type: employs
  description: The prompt instructed the AI agent to read the user's SSH keys at `~/.ssh/id_rsa`.
  tactic: AML.TA0013
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0054
  target: AML.T0065
  relationship-type: employs
  description: The researchers crafted a prompt that instructs an AI agent to discover
    and read user credentials files and store them in an input parameter of an MCP
    tool.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0054
  target: AML.T0086
  relationship-type: employs
  description: The prompt instructed the AI agent to store the credentials files in
    an extraneous MCP tool parameter to exfiltrate them via the MCP connection.
  tactic: AML.TA0010
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0054
  target: AML.T0098
  relationship-type: employs
  description: The prompt instructed the AI agent to read `mcp.json`, which often
    contains credentials for other MCP servers.
  tactic: AML.TA0013
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0054
  target: AML.T0104
  relationship-type: employs
  description: The researchers hosted a poisoned MCP server that contains the malicious
    instructions hidden in the docstring of one of the provided tools.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: Data Exfiltration via Remote Poisoned MCP Tool
references:
- id: ref-1
  title: 'MCP Security Notification: Tool Poisoning Attacks'
  url: https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
created-date: '2026-03-31'
modified-date: '2026-03-31'
type: Exercise
actor: Invariant Labs
target: Model Context Protocol
date: '2025-04-01'
date-granularity: Day
id: AML.CS0054
uuid: 6ef6af8c-7c49-521b-8177-1e969238f7bd
object-type: case-study
```
