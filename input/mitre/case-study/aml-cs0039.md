---
title: 'Living Off AI: Prompt Injection via Jira Service Management'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-26'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0039
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0039
object_type: case-study
---

# AML.CS0039: Living Off AI: Prompt Injection via Jira Service Management

## Description

Researchers from Cato Networks demonstrated how adversaries can exploit AI-powered systems embedded in enterprise workflows to execute malicious actions with elevated privileges. This is achieved by crafting malicious inputs from external users such as support tickets that are later processed by internal users or automated systems using AI agents. These AI agents, operating with internal context and trust, may interpret and execute the malicious instructions, leading to unauthorized actions such as data exfiltration, privilege escalation, or system manipulation.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0039
  target: AML.T0003
  relationship-type: employs
  description: The researchers performed reconnaissance to learn about Atlassian's
    Model Context Protocol (MCP) server and its integration into the Jira Service
    Management (JSM) platform. Atlassian offers an MCP server, which embeds AI into
    enterprise workflows. Their MCP enables a range of AI-driven actions, such as
    ticket summarization, auto-replies, classification, and smart recommendations
    across JSM and Confluence. It allows support engineers and internal users to interact
    with AI directly from their native interfaces.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0039
  target: AML.T0051.001
  relationship-type: employs
  description: As part of their standard workflow, a support engineer at the victim
    organization used Claude Sonnet (which can interact with Jira via the Atlassian
    MCP server) to help them resolve the malicious ticket, causing the injection to
    be unknowingly executed.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0039
  target: AML.T0053
  relationship-type: employs
  description: The malicious prompt requested information accessible to the AI agent
    via Atlassian MCP tools, causing those tools to be invoked via MCP, granting the
    researchers increased privileges on the victim's JSM instance.
  tactic: AML.TA0012
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0039
  target: AML.T0065
  relationship-type: employs
  description: The researchers crafted a malicious prompt that requests data from
    all other support tickets be posted as a reply to the current ticket.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0039
  target: AML.T0085.001
  relationship-type: employs
  description: The malicious prompt instructed that all details of other issues be
    collected. This invoked an Atlassian MCP tool that could access the Jira tickets
    and collect them.
  tactic: AML.TA0009
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0039
  target: AML.T0086
  relationship-type: employs
  description: The malicious prompt instructed that the collected ticket details be
    posted in a reply to the ticket. This invoked an Atlassian MCP Tool which performed
    the requested action, exfiltrating the data where it was accessible to the researchers
    on the JSM portal.
  tactic: AML.TA0010
  step-id: S07
  leads-to: []
- source: AML.CS0039
  target: AML.T0093
  relationship-type: employs
  description: The researchers created a new service ticket containing the malicious
    prompt on the public Jira Service Management (JSM) portal of the victim identified
    during reconnaissance.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0039
  target: AML.T0095
  relationship-type: employs
  description: The researchers used a search query, "site:atlassian.net/servicedesk
    inurl:portal",  to reveal organizations using Atlassian service portals as potential
    targets.
  tactic: AML.TA0002
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: 'Living Off AI: Prompt Injection via Jira Service Management'
references:
- id: ref-1
  title: 'Cato CTRL Threat Research: PoC Attack Targeting Atlassian''s Model Context
    Protocol (MCP) Introduces New "Living Off AI" Risk'
  url: https://www.catonetworks.com/blog/cato-ctrl-poc-attack-targeting-atlassians-mcp/
created-date: '2025-11-07'
modified-date: '2025-11-26'
type: Exercise
actor: Cato CTRL
target: Atlassian MCP, Jira Service Management
date: '2025-06-19'
date-granularity: Day
id: AML.CS0039
uuid: 3f1df6b6-378d-5fef-b964-cbbb9fff6ce5
object-type: case-study
```
