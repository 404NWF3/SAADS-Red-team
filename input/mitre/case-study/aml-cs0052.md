---
title: 'LLMSmith: RCE Vulnerabilities in LLM-Integrated Applications'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0052
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0052
object_type: case-study
---

# AML.CS0052: LLMSmith: RCE Vulnerabilities in LLM-Integrated Applications

## Description

Researchers identified 20 remote code execution (RCE) vulnerabilities across 11 different LLM frameworks. They discovered applications deployed on the public internet built using these LLM frameworks and demonstrated the RCE vulnerabilities could be exploited using prompt injection.

The 11 LLM frameworks the researchers evaluated were: LangChain, LlamaIndex, Pandas-ai, Langflow, Pandas-llm, Auto-GPT, Griptape, Lagent, MetaGPT, vanna,  and langroid.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0052
  target: AML.T0004
  relationship-type: employs
  description: The researchers performed targeting to identify applications that are
    likely built on with LLM Frameworks and may use the functions vulnerable to RCE.
    This was done by scanning source code repositories for app deployment URLs.
  tactic: AML.TA0002
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0052
  target: AML.T0017
  relationship-type: employs
  description: The researchers performed a static analysis on the APIs of target LLM
    frameworks to identify functions that execute code from either user input or the
    response from an LLM and are thus vulnerable to RCE.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0052
  target: AML.T0049
  relationship-type: employs
  description: The researchers targeted public-facing applications that expose an
    AI agent to user input as a means to execute their prompts.
  tactic: AML.TA0004
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0052
  target: AML.T0050
  relationship-type: employs
  description: The code included in the researcher's prompts was executed in a sandboxed
    Python interpreter.
  tactic: AML.TA0005
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0052
  target: AML.T0051.000
  relationship-type: employs
  description: The researchers directly prompted the AI agent with their malicious
    instructions.
  tactic: AML.TA0005
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0052
  target: AML.T0053
  relationship-type: employs
  description: The researchers' prompts called the AI agent's tools, targeting call
    chains that can lead to code execution.
  tactic: AML.TA0012
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0052
  target: AML.T0054
  relationship-type: employs
  description: For target applications where the AI agent refused the researcher's
    request, they used lightweight jailbreaking strategies to bypass the LLM's guardrails.
  tactic: AML.TA0007
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0052
  target: AML.T0065
  relationship-type: employs
  description: The researchers developed prompts to trigger tool invocations that
    lead to RCE.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0052
  target: AML.T0072
  relationship-type: employs
  description: The Python code opened a reverse shell which was used as a command
    and control channel.
  tactic: AML.TA0014
  step-id: S10
  leads-to:
  - S11
- source: AML.CS0052
  target: AML.T0084.003
  relationship-type: employs
  description: The researchers ran their static analysis to extract call chains from
    target application's source code to identify those that utilize LLM framework
    functions vulnerable to RCE.
  tactic: AML.TA0008
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0052
  target: AML.T0105
  relationship-type: employs
  description: The researchers included code escape techniques designed to bypass
    any limitations a sandbox may place on code execution.
  tactic: AML.TA0012
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0052
  target: AML.T0112.000
  relationship-type: employs
  description: The researchers gained full control of the system running the LLM-integrated
    application.
  tactic: AML.TA0011
  step-id: S11
  leads-to: []
```

## Structured source fields

```yaml
name: 'LLMSmith: RCE Vulnerabilities in LLM-Integrated Applications'
references:
- id: ref-1
  title: Demystifying RCE Vulnerabilities in LLM-Integrated Apps
  url: https://arxiv.org/abs/2309.02926
- id: ref-2
  title: LLMSmith Website
  url: https://sites.google.com/view/llmsmith
created-date: '2026-03-31'
modified-date: '2026-03-31'
type: Exercise
actor: Researchers at University of Chinese Academy of Sciences, Shandong University,
  and University of New South Wales
target: LLM Integration Frameworks
date: '2025-02-27'
date-granularity: Day
id: AML.CS0052
uuid: fbab9867-cbfa-5fec-84fa-c57c549ed545
object-type: case-study
```
