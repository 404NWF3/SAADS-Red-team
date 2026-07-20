---
title: Data Exfiltration via an MCP Server used by Cursor
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-01-30'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0045
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0045
object_type: case-study
---

# AML.CS0045: Data Exfiltration via an MCP Server used by Cursor

## Description

The Backslash Security Research Team demonstrated that a Model Context Protocol (MCP) tool can be used as a vector for an indirect prompt injection attack on Cursor, potentially leading to the execution of malicious shell commands.

The Backslash Security Research Team created a proof-of-concept MCP server capable of scraping webpages. When a user asks Cursor to use the tool to scrape a site containing a malicious prompt, the prompt is injected into Cursor's context. The prompt instructs Cursor to execute a shell command to exfiltrate the victim's AI agent configuration files containing credentials. Cursor does prompt the user before executing the malicious command, potentially mitigating the attack.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0045
  target: AML.T0048.000
  relationship-type: employs
  description: A bad actor could use the stolen credentials cause financial damage
    and could also steal other sensitive information from the victim user.
  tactic: AML.TA0011
  step-id: S10
  leads-to: []
- source: AML.CS0045
  target: AML.T0051.001
  relationship-type: employs
  description: When the MCP server scraped the malicious web site, it returned the
    injected prompt to the MCP client and poisoned the context of the Cursor LLM.
    Cursor executed the malicious prompt embedded in the website scraped by the MCP
    tool.
  tactic: AML.TA0005
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0045
  target: AML.T0053
  relationship-type: employs
  description: 'The prompt injection invoked Cursor''s ability to call command line
    tools via the `run_terminal_cmd` tool.


    Cursor prompted the user before executing a shell command, potentially mitigating
    this attack.'
  tactic: AML.TA0012
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0045
  target: AML.T0065
  relationship-type: employs
  description: The researchers crafted a malicious prompt containing an instruction
    to execute the malicious shell command to exfiltrate the victim's AI agent credentials.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0045
  target: AML.T0068
  relationship-type: employs
  description: The malicious prompt was hidden in the title tag of the webpage.
  tactic: AML.TA0007
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0045
  target: AML.T0068
  relationship-type: employs
  description: When the MCP server scraped the malicious web site, it returned the
    injected prompt to the MCP client and poisoned the context of the Cursor LLM.
    The shell command in the malicious prompt was obscured via base64 encoding, making
    it less clear to the user that something malicious may be executed.
  tactic: AML.TA0007
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0045
  target: AML.T0078
  relationship-type: employs
  description: When a user asked Cursor to use an MCP tool to scrape the malicious
    website, the contents of the malicious prompt was retrieved and ingested into
    Cursor's context window.
  tactic: AML.TA0004
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0045
  target: AML.T0079
  relationship-type: employs
  description: The researchers created a malicious web site containing the malicious
    prompt.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0045
  target: AML.T0079
  relationship-type: employs
  description: The researchers launched a web server to receive data exfiltrated from
    the victim.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0045
  target: AML.T0083
  relationship-type: employs
  description: The shell command located the `.openapi.apiKey` and `.cursor/mcp.json`
    credentials files that were part of the Cursor's configuration.
  tactic: AML.TA0013
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0045
  target: AML.T0086
  relationship-type: employs
  description: The credentials files were exfiltrated to the researcher's server via
    a `curl` command invoked by Cursor's `run_terminal_cmd` tool.
  tactic: AML.TA0010
  step-id: S09
  leads-to:
  - S10
```

## Structured source fields

```yaml
name: Data Exfiltration via an MCP Server used by Cursor
references:
- id: ref-1
  title: 'Simulating a Context-Poisoning Vulnerable MCP Server: A POC'
  url: https://www.backslash.security/blog/simulating-a-vulnerable-mcp-server-for-context-poisoning
created-date: '2026-01-30'
modified-date: '2026-01-30'
type: Exercise
actor: Backslash Security Research Team
target: Cursor
date: '2025-06-24'
date-granularity: Day
id: AML.CS0045
uuid: b6e0664a-0d96-5455-84c1-78d14d89c84d
object-type: case-study
```
