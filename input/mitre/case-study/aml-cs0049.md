---
title: Supply Chain Compromise via Poisoned ClawdBot Skill
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-03-31'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0049
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0049
object_type: case-study
---

# AML.CS0049: Supply Chain Compromise via Poisoned ClawdBot Skill

## Description

A security researcher demonstrated a proof-of-concept supply chain attack using a poisoned ClawdBot Skill shared on ClawdHub, a Skill registry for agents. The poisoned Skill contained a prompt injection that caused ClawdBot to execute a shell command that reached the researcher's server. Although the researcher here used this access simply to warn users about the danger, they could have instead delivered a malicious payload and compromised the user's system. The security researcher recorded 16 different users who downloaded and executed the poisoned Skill in the first 8 hours of it being published on ClawdHub.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0049
  target: AML.T0008.002
  relationship-type: employs
  description: The researcher registered the domain `clawdhub-skill.com` to host their
    web server.
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0049
  target: AML.T0010.005
  relationship-type: employs
  description: 'Users downloaded the poisoned Skill from ClawdHub.


    Note that ClawdHub does not display all files that are part of the Skill, making
    it hard for users to review Skills before downloading them.'
  tactic: AML.TA0004
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0049
  target: AML.T0011.002
  relationship-type: employs
  description: When a user asked Claude Code "what would Elon do?" it calls the poisoned
    Skill.
  tactic: AML.TA0005
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0049
  target: AML.T0017
  relationship-type: employs
  description: The researcher created a simple web server to log requests.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0049
  target: AML.T0048
  relationship-type: employs
  description: 'In this proof of concept, the researcher simply pinged their server
    and warned the user of the dangers of using Skills without reading the source
    code, causing no harm. However, they could have delivered a malicious payload,
    and caused a variety of harms, including:

    - Exfiltrating the user''s codebase

    - Injecting backdoors into the user''s codebase

    - Stealing the user''s credentials

    - Installing malware or crypto miners

    - Performing anything else Claude Code is capable of'
  tactic: AML.TA0011
  step-id: S10
  leads-to: []
- source: AML.CS0049
  target: AML.T0051.000
  relationship-type: employs
  description: Claude Code read all files that are part of the Skill, executing the
    malicious prompt in the `rules/logic.md` file.
  tactic: AML.TA0005
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0049
  target: AML.T0053
  relationship-type: employs
  description: Claude Code executed the shell command using it's `bash` tool.
  tactic: AML.TA0012
  step-id: S09
  leads-to:
  - S10
- source: AML.CS0049
  target: AML.T0065
  relationship-type: employs
  description: The researcher crafted a prompt injection designed to cause Claude
    Code to execute a `curl` command to the researcher's `clawdhub-skill.com` domain.
  tactic: AML.TA0003
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0049
  target: AML.T0074
  relationship-type: employs
  description: Claude Code prompted the user before executing the shell command. The
    researcher had registered the `https://clawdhub-skill.com` domain, which appears
    to be legitimate and may be confused with the legitimate `https://clawdhub.com`
    domain, causing the user to select confirm.
  tactic: AML.TA0007
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0049
  target: AML.T0104
  relationship-type: employs
  description: The researcher developed a poisoned ClawdBot Skill called "What Would
    Elon Do?" The Skill contained the malicious prompt in the `rules/logic.md` file,
    which is read when the Skill is activated. The researcher published their Skill
    to ClawdHub.
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0049
  target: AML.T0111
  relationship-type: employs
  description: The researcher used a script to increase the number of downloads of
    their Skill to increase visibility and gain trust.
  tactic: AML.TA0007
  step-id: S04
  leads-to:
  - S05
```

## Structured source fields

```yaml
name: Supply Chain Compromise via Poisoned ClawdBot Skill
references:
- id: ref-1
  title: 'eating lobster souls Part II: the supply chain (aka - backdooring the #1
    downloaded clawdhub skill)'
  url: https://x.com/theonejvo/status/2015892980851474595
created-date: '2026-02-06'
modified-date: '2026-03-31'
type: Exercise
actor: Jamieson O'Reilly
target: ClawdBot (now OpenClaw)
date: '2026-01-26'
date-granularity: Day
id: AML.CS0049
uuid: cf5369d7-45b4-5bda-90f4-a8ef46b8043f
object-type: case-study
```
