---
title: 'EchoLeak: Zero-Click Prompt Injection Targeting M365 Copilot for Data Exfiltration'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-06-30'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0059
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0059
object_type: case-study
---

# AML.CS0059: EchoLeak: Zero-Click Prompt Injection Targeting M365 Copilot for Data Exfiltration

## Description

Aim Security researchers discovered EchoLeak, a zero-click vulnerability in Microsoft 365 Copilot that could allow an attacker to exfiltrate sensitive enterprise data without user interaction.

The attack used a prompt injection delivered via an email sent to a target user. When M365 Copilot retrieved the email as part of its retrieval-augmented generation (RAG) context, the malicious instructions caused Copilot to search the user's accessible Microsoft 365 data and include sensitive information in its response context. The sensitive information was then exfiltrated via requests to attacker-controlled URLs without requiring the victim to open the email or click a link.

The attack chain bypassed multiple protections, including prompt injection defenses, link redaction, and content security policy restrictions.

Microsoft assigned the issue CVE-2025-32711[[cve-2025-32711]]. It has since been remediated with no evidence it was exploited in the wild.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0059
  target: AML.T0025
  relationship-type: employs
  description: To bypass CSP restrictions, the researchers routed the rendered image
    request through an allowed Microsoft Teams preview or proxy path, which fetched
    the attacker-controlled URL containing the encoded secret.
  tactic: AML.TA0010
  step-id: S10
  leads-to:
  - S11
- source: AML.CS0059
  target: AML.T0048
  relationship-type: employs
  description: If exploited against a real enterprise user, the attack could disclose
    confidential business data and harm the organization or affected users.
  tactic: AML.TA0011
  step-id: S11
  leads-to: []
- source: AML.CS0059
  target: AML.T0051.002
  relationship-type: employs
  description: When the user later invoked Copilot, which retrieved the malicious
    email into its context and triggering the prompt injection.
  tactic: AML.TA0005
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0059
  target: AML.T0065
  relationship-type: employs
  description: The researchers crafted malicious instructions designed to evade Microsoft's
    indirect prompt injection classifier, appear like ordinary business content, suppress
    attribution to the attacker-controlled email, and cause Copilot to include sensitive
    data in rendered output.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0059
  target: AML.T0066
  relationship-type: employs
  description: The researchers embedded the prompt injection in business-like email
    content that was likely to be retrieved during a later Copilot interaction. The
    content was designed to appear relevant to ordinary enterprise workflows while
    carrying hidden instructions.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0059
  target: AML.T0067
  relationship-type: employs
  description: The output was manipulated to avoid obvious attribution and to use
    reference-style Markdown links or images that bypassed link redaction.
  tactic: AML.TA0007
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0059
  target: AML.T0068
  relationship-type: employs
  description: The prompt was phrased as benign business text rather than and obviously
    malicious prompt to evade user suspicion.
  tactic: AML.TA0007
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0059
  target: AML.T0070
  relationship-type: employs
  description: The email was automatically ingested into a RAG database available
    to Copilot's retrieval pipeline.
  tactic: AML.TA0006
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0059
  target: AML.T0077
  relationship-type: employs
  description: Copilot rendered a Markdown image whose URL encoded sensitive information.
    The client automatically attempted to fetch the image, creating a zero-click exfiltration
    path.
  tactic: AML.TA0010
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0059
  target: AML.T0079
  relationship-type: employs
  description: The researchers staged an attacker-controlled web endpoint to receive
    outbound requests containing encoded sensitive data. The endpoint served as the
    collection point for the exfiltration channel.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0059
  target: AML.T0085.000
  relationship-type: employs
  description: The malicious instructions caused Copilot to access sensitive enterprise
    information available through the user's Microsoft 365 account, such as emails,
    files, or project details.
  tactic: AML.TA0009
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0059
  target: AML.T0093
  relationship-type: employs
  description: The researchers sent the email to a Microsoft 365 user inbox.
  tactic: AML.TA0004
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: 'EchoLeak: Zero-Click Prompt Injection Targeting M365 Copilot for Data Exfiltration'
references:
- id: echoleak-paper
  title: 'EchoLeak: The First Real-World Zero-Click Prompt Injection Exploit in a
    Production LLM System'
  url: https://arxiv.org/abs/2509.10540
- id: cve-2025-32711
  title: CVE-2025-32711
  url: https://www.cve.org/CVERecord?id=CVE-2025-32711
- id: cato
  title: Breaking down 'EchoLeak', the First Zero-Click AI Vulnerability Enabling
    Data Exfiltration from Microsoft 365 Copilot
  url: https://www.catonetworks.com/blog/breaking-down-echoleak/
created-date: '2026-06-30'
modified-date: '2026-06-30'
type: Exercise
actor: Aim Labs
target: Microsoft 365 Copilot
date: '2025-05-25'
date-granularity: Month
id: AML.CS0059
uuid: f5621f28-870b-5330-8cc2-d95cee1ebaf0
object-type: case-study
```
