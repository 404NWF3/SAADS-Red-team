---
title: 'LAMEHUG: Malware Leveraging Dynamic AI-Generated Commands'
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0044
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0044
object_type: case-study
---

# AML.CS0044: LAMEHUG: Malware Leveraging Dynamic AI-Generated Commands

## Description

In July 2025, Ukrainian authorities reported the emergence of LAMEHUG, a new AI-powered malware attributed to the Russian state-backed threat actor [APT28](https://attack.mitre.org/groups/G0007/) (also tracked as Forest Blizzard or UAC-0001). LAMEHUG uses a large language model (LLM) to dynamically generate commands on the infected hosts.

The campaign began with a phishing attack leveraging a compromised government email account to deliver a malicious ZIP archive disguised as Appendix.pdf.zip. The archive contained the LAMEHUG malware, a Python-based executable, packed with PyInstaller. When executed, the malware, makes calls to an LLM endpoint to generate malicious from natural language prompts. Dynamically generated commands may make the malware harder to detect. LAMEHUG was configured to collect files from the local system and exfiltrate them.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0044
  target: AML.T0011
  relationship-type: employs
  description: The attachment contained an executable file with a .pif extension,
    created using PyInstaller from Python source code which CERT-UA classified it
    as LAMEHUG malware. Files with the .pif extension are executable on Windows.
  tactic: AML.TA0005
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0044
  target: AML.T0012
  relationship-type: employs
  description: APT28 gained access to a compromised official email account.
  tactic: AML.TA0004
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0044
  target: AML.T0025
  relationship-type: employs
  description: The LAMEHUG malware exfiltrated collected data to attacker controlled
    servers via SFTP or HTTP POST requests.
  tactic: AML.TA0010
  step-id: S07
  leads-to: []
- source: AML.CS0044
  target: AML.T0037
  relationship-type: employs
  description: The LAMEHUG malware used the AI generated commands to collect system
    information (saved to `%PROGRAMDATA%\info\info.txt`) and recursively searched
    Documents, Desktop, and Downloads to stage files for exfiltration.
  tactic: AML.TA0009
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0044
  target: AML.T0052
  relationship-type: employs
  description: APT28 sent a phishing email from the compromised account with an attachment
    containing malware.
  tactic: AML.TA0015
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0044
  target: AML.T0073
  relationship-type: employs
  description: The email impersonated a government ministry representative.
  tactic: AML.TA0007
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0044
  target: AML.T0074
  relationship-type: employs
  description: The attachment was called "Appendix.pdf.zip" which could confuse the
    recipient into thinking it was a legitimate PDF file.
  tactic: AML.TA0007
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0044
  target: AML.T0102
  relationship-type: employs
  description: The LAMEHUG malware abused the Qwen 2.5 Coder 32B Instruct model Hugging
    Face API to generate malicious commands from natural language prompts.
  tactic: AML.TA0001
  step-id: S05
  leads-to:
  - S06
```

## Structured source fields

```yaml
name: 'LAMEHUG: Malware Leveraging Dynamic AI-Generated Commands'
references:
- id: bleepingcomputer
  title: LameHug malware uses AI LLM to craft Windows data-theft commands in real-time
  url: https://www.bleepingcomputer.com/news/security/lamehug-malware-uses-ai-llm-to-craft-windows-data-theft-commands-in-real-time/
- id: cert
  title: UAC-0001 cyberattacks on the security and defense sector using the LAMEHUG
    software tool, which uses LLM (large language model) (CERT-UA#16039)
  url: https://cert.gov.ua/article/6284730
- id: logpoint
  title: 'APT28''s New Arsenal: LAMEHUG, the First AI-Powered Malware'
  url: https://logpoint.com/en/blog/apt28s-new-arsenal-lamehug-the-first-ai-powered-malware
created-date: '2025-12-24'
modified-date: '2026-03-31'
type: Incident
actor: APT28
target: Ukraine's security and defense sector
reporter: CERT-UA
date: '2025-06-03'
date-granularity: Month
id: AML.CS0044
uuid: 77a64f02-fde8-5773-a319-455da5f8fd39
object-type: case-study
```
