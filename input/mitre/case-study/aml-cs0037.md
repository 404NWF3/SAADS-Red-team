---
title: Data Exfiltration via Agent Tools in Copilot Studio
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-11-26'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0037
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0037
object_type: case-study
---

# AML.CS0037: Data Exfiltration via Agent Tools in Copilot Studio

## Description

Researchers from Zenity demonstrated how an organization's data can be exfiltrated via prompt injections that target an AI-powered customer service agent.

The target system is a customer service agent built by Zenity in Copilot Studio. It is modeled after an agent built by McKinsey to streamline its customer service needs. The AI agent listens to a customer service email inbox where customers send their engagement requests. Upon receiving a request, the agent looks at the customer's previous engagements, understands who the best consultant for the case is, and proceeds to send an email to the respective consultant regarding the request, including all of the relevant context the consultant will need to properly engage with the customer.

The Zenity researchers begin by performing targeting to identify an email inbox that is managed by an AI agent. Then they use prompt injections to discover details about the AI agent, such as its knowledge sources and tools. Once they understand the AI agent's capabilities, the researchers are able to craft a prompt that retrieves private customer data from the organization's RAG database and CRM, and exfiltrate it via the AI agent's email tool.

Vendor Response: Microsoft quickly acknowledged and fixed the issue. The prompts used by the Zenity researchers in this exercise no longer work, however other prompts may still be effective.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0037
  target: AML.T0006
  relationship-type: employs
  description: The researchers look for support email addresses on the target organization's
    website which may be managed by an AI agent. Then, they probe the system by sending
    emails and looking for indications of agentic AI in automatic replies.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0037
  target: AML.T0047
  relationship-type: employs
  description: From here, the researchers repeat the same steps to interact with the
    AI agent, sending malicious prompts to the agent via email and receiving responses
    at their desired address.
  tactic: AML.TA0000
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0037
  target: AML.T0051
  relationship-type: employs
  description: The researchers modify the original prompt to discover other knowledge
    sources and tools that may have data they are after.
  tactic: AML.TA0005
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0037
  target: AML.T0051.002
  relationship-type: employs
  description: The researchers receive a reply at the address they specified, indicating
    that there is an AI agent present, and that the triggered prompt injection was
    successful.
  tactic: AML.TA0005
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0037
  target: AML.T0065
  relationship-type: employs
  description: Once a target has been identified, the researchers craft prompts designed
    to probe for a potential AI agent monitoring the inbox. The prompt instructs the
    agent to send an email reply to an address of the researchers' choosing.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0037
  target: AML.T0065
  relationship-type: employs
  description: The researchers put their knowledge of the AI agent's tools and knowledge
    sources together to craft a prompt that will collect and exfiltrate the customer
    data they are after.
  tactic: AML.TA0003
  step-id: S10
  leads-to:
  - S11
- source: AML.CS0037
  target: AML.T0084.000
  relationship-type: employs
  description: The researchers discover the AI agent has access to a "Customer Support
    Account Owners.csv" data source.
  tactic: AML.TA0008
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0037
  target: AML.T0084.001
  relationship-type: employs
  description: The researchers infer that the AI agent has a tool for sending emails.
  tactic: AML.TA0008
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0037
  target: AML.T0084.001
  relationship-type: employs
  description: The researchers discover the AI agent has access to the Salesforce
    get-records tool, which can be used to retrieve CRM records.
  tactic: AML.TA0008
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0037
  target: AML.T0084.002
  relationship-type: employs
  description: The researchers infer that the AI agent is activated when receiving
    an email.
  tactic: AML.TA0008
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0037
  target: AML.T0085.000
  relationship-type: employs
  description: The prompt asks the agent to retrieve all of the fields and rows from
    "Customer Support Account Owners.csv". The agent retrieves the entire file.
  tactic: AML.TA0009
  step-id: S11
  leads-to:
  - S12
- source: AML.CS0037
  target: AML.T0085.001
  relationship-type: employs
  description: The prompt asks the agent to retrieve all Salesforce records using
    its get-records tool. The agent retrieves all records from the victim's CRM.
  tactic: AML.TA0009
  step-id: S12
  leads-to:
  - S13
- source: AML.CS0037
  target: AML.T0086
  relationship-type: employs
  description: The prompt asks the agent to email the results to an address of the
    researcher's choosing using its email tool. The researchers successfully exfiltrate
    their target data via the tool invocation.
  tactic: AML.TA0010
  step-id: S13
  leads-to: []
- source: AML.CS0037
  target: AML.T0093
  relationship-type: employs
  description: The researchers send an email with the malicious prompt to the inbox
    they suspect may be managed by an AI agent.
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
```

## Structured source fields

```yaml
name: Data Exfiltration via Agent Tools in Copilot Studio
references:
- id: ref-1
  title: 'AgentFlayer: Discovery Phase of AI Agents in Copilot Studio'
  url: https://labs.zenity.io/p/a-copilot-studio-story-discovery-phase-in-ai-agents-f917
- id: ref-2
  title: 'AgentFlayer: When AIjacking Leads to Full Data Exfiltration in Copilot Studio'
  url: https://labs.zenity.io/p/a-copilot-studio-story-2-when-aijacking-leads-to-full-data-exfiltration-bc4a
created-date: '2025-11-07'
modified-date: '2025-11-26'
type: Exercise
actor: Zenity
target: Copilot Studio Customer Service Agent
date: '2025-06-01'
date-granularity: Month
id: AML.CS0037
uuid: 13f74111-0fc9-58c2-9b23-e9af136ab0b2
object-type: case-study
```
