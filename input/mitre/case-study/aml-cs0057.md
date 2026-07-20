---
title: Storm-2139 Azure OpenAI Guardrail Bypass
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-06-30'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0057
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0057
object_type: case-study
---

# AML.CS0057: Storm-2139 Azure OpenAI Guardrail Bypass

## Description

Storm-2139 built custom jailbreak tooling to bypass guardrails on Azure OpenAI Services, allowing users to generate harmful synthetic content.

Microsoft reported that members of Storm-2139 scraped exposed customer credentials from public sources and used them to access accounts for generative AI services. The group developed and operated tools and services that bypassed safety safeguards, modified service capabilities, and enabled end users to generate harmful and illicit content, including non-consensual intimate images of celebrities and other sexually explicit content.

The operation included creators who developed illicit tools, providers who modified and supplied those tools, and users who generated prohibited content. Microsoft pursued civil legal action.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0057
  target: AML.T0008
  relationship-type: employs
  description: Storm-2139 acquired infrastructure to support a service that sold access
    to the jailbroken Azure OpenAI Service.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0057
  target: AML.T0012
  relationship-type: employs
  description: Storm-2139 used exposed customer credentials scraped from public sources
    to access valid accounts for generative AI services.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0057
  target: AML.T0017
  relationship-type: employs
  description: Storm-2139 creators developed a tool called de3u to facilitate unauthorized
    use of generative AI services and bypass safeguards.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0057
  target: AML.T0040
  relationship-type: employs
  description: The stolen credentials provided access Azure OpenAI Service, allowing
    the actors and their customers to submit prompts and generate content. Storm-2139's
    de3u tool was used as the frontend for this access.
  tactic: AML.TA0000
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0057
  target: AML.T0048.000
  relationship-type: employs
  description: Users whose accounts were stolen were harmed financially.
  tactic: AML.TA0011
  step-id: S08
  leads-to: []
- source: AML.CS0057
  target: AML.T0048.002
  relationship-type: employs
  description: The generated abusive imagery could cause direct harm to depicted individuals.
  tactic: AML.TA0011
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0057
  target: AML.T0054
  relationship-type: employs
  description: Storm-2139 deliberately bypassed Azure OpenAI Service safeguards and
    content filters to generate prohibited outputs. Microsoft reported that the actors
    iterated on blocked prompts, substituted celebrity descriptions, and used altered
    wording or technical notation to evade filters.
  tactic: AML.TA0007
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0057
  target: AML.T0079
  relationship-type: employs
  description: Storm-2139 staged and operated a reverse proxy service to allow other
    malicious users to interact with abused generative AI services.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0057
  target: AML.T0088
  relationship-type: employs
  description: End users generated abusive synthetic imagery, including non-consensual
    intimate images of celebrities and other sexually explicit, misogynistic, violent,
    or hateful content.
  tactic: AML.TA0001
  step-id: S06
  leads-to:
  - S07
```

## Structured source fields

```yaml
name: Storm-2139 Azure OpenAI Guardrail Bypass
references:
- id: microsoft-jan-2025
  title: Taking legal action to protect the public from abusive AI-generated content
  url: https://blogs.microsoft.com/on-the-issues/2025/01/10/taking-legal-action-to-protect-the-public-from-abusive-ai-generated-content/
- id: microsoft-feb-2025
  title: Disrupting a global cybercrime network abusing generative AI
  url: https://blogs.microsoft.com/on-the-issues/2025/02/27/disrupting-cybercrime-abusing-gen-ai/
- id: microsoft-may-2025
  title: How Microsoft is taking down AI hackers who create harmful images of celebrities
    and others
  url: https://news.microsoft.com/source/features/ai/how-microsoft-is-taking-down-ai-hackers-who-create-harmful-images-of-celebrities-and-others/
created-date: '2026-06-30'
modified-date: '2026-06-30'
type: Incident
actor: Storm-2139
target: Microsoft Azure OpenAI Service
reporter: Microsoft
date: '2024-12-01'
date-granularity: Month
id: AML.CS0057
uuid: cd6e0f2f-65ce-54c5-adfd-e7099a2f1ada
object-type: case-study
```
