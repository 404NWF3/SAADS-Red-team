---
title: Poisoned Postmark MCP Server Email Exfiltration
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0053
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0053
object_type: case-study
---

# AML.CS0053: Poisoned Postmark MCP Server Email Exfiltration

## Description

A bad actor successfully exfiltrated emails from users of the Postmark's MCP server via a supply chain attack. Postmark is an email delivery service that allows organizations to send marketing and transactional emails via API. The Postmark MCP server allows users to interact with Postmark via AI agents.

The bad actor impersonated Postmark, by registering the `postmark-mcp` package name on npm. They initially published the legitimate versions of the MCP server. After the package became popular and reached over 1,000 downloads per week, the bad actor performed a rugpull and uploaded a malicious version of the package. The malicious version added the bad actor's email address in the BCC line of all emails sent by the MCP tool. Users who upgraded to this version and continued to use the tool would have all emails exfiltrated to the bad actor.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0053
  target: AML.T0010.005
  relationship-type: employs
  description: When organizations upgraded `postmark-mcp` to version `1.0.16`, they
    received the malicious version of the tool via the compromised supply chain.
  tactic: AML.TA0004
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0053
  target: AML.T0011.002
  relationship-type: employs
  description: When users at the victim organization instructed their AI agent to
    use tools provided by the poisoned Postmark MCP Server, the malicious code was
    executed.
  tactic: AML.TA0005
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0053
  target: AML.T0017
  relationship-type: employs
  description: The bad actor modified the legitimate Postmark MCP server to include
    their email address on the BCC line on all emails sent by the tool.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0053
  target: AML.T0048
  relationship-type: employs
  description: The exfiltrated emails may include transactional emails (revealing
    private information about the organization's clients) and promotional emails (revealing
    the organization's client list).
  tactic: AML.TA0011
  step-id: S08
  leads-to: []
- source: AML.CS0053
  target: AML.T0073
  relationship-type: employs
  description: The bad actor impersonated Postmark by publishing a legitimate version
    of their `postmark-mcp` package to npm.  Postmark had not registered the `postmark-mcp`
    name on npm themselves, allowing the bad actor to namesquat. Legitimate users
    were tricked into using the npm package even though it wasn't managed by the official
    developers of `postmark-mcp`
  tactic: AML.TA0007
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0053
  target: AML.T0086
  relationship-type: employs
  description: When organizations sent emails via the `postmark-mcp` tool, the entire
    contents of their emails are exfiltrated to the bad actor via the address added
    on the BCC line.
  tactic: AML.TA0010
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0053
  target: AML.T0104
  relationship-type: employs
  description: The bad actor published their malicious version of `postmark-mcp` to
    npm.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0053
  target: AML.T0109
  relationship-type: employs
  description: By waiting for users to adopt a legitimate version of `postmark-mcp`
    first, the bad actor was able to evade the additional scrutiny and scanning performed
    on new tools.
  tactic: AML.TA0007
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0053
  target: AML.T0110
  relationship-type: employs
  description: Once configured with the organization's AI agents, the poisoned Postmark
    MCP server's effects persist.
  tactic: AML.TA0006
  step-id: S05
  leads-to:
  - S06
```

## Structured source fields

```yaml
name: Poisoned Postmark MCP Server Email Exfiltration
references:
- id: ref-1
  title: 'First Malicious MCP in the Wild: The Postmark Backdoor That''s Stealing
    Your Emails'
  url: https://www.koi.ai/blog/postmark-mcp-npm-malicious-backdoor-email-theft
created-date: '2026-03-31'
modified-date: '2026-03-31'
type: Incident
actor: Unknown Bad Actor
target: Postmark MCP Server
reporter: Koi Research
date: '2025-09-01'
date-granularity: Month
id: AML.CS0053
uuid: 07d14997-fa16-5626-8940-8fc291ba172f
object-type: case-study
```
