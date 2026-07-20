---
title: ShadowRay
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0023
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0023
object_type: case-study
---

# AML.CS0023: ShadowRay

## Description

Ray is an open-source Python framework for scaling production AI workflows. Ray's Job API allows for arbitrary remote execution by design. However, it does not offer authentication, and the default configuration may expose the cluster to the internet. Researchers at Oligo discovered that Ray clusters have been actively exploited for at least seven months. Adversaries can use victim organization's compute power and steal valuable information. The researchers estimate the value of the compromised machines to be nearly 1 billion USD.

Five vulnerabilities in Ray were reported to Anyscale, the maintainers of Ray. Anyscale promptly fixed four of the five vulnerabilities. However, the fifth vulnerability [CVE-2023-48022](https://nvd.nist.gov/vuln/detail/CVE-2023-48022) remains disputed. Anyscale maintains that Ray's lack of authentication is a design decision, and that Ray is meant to be deployed in a safe network environment. The Oligo researchers deem this a "shadow vulnerability" because in disputed status, the CVE does not show up in static scans.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0023
  target: AML.T0006
  relationship-type: employs
  description: Adversaries can scan for public IP addresses to identify those potentially
    hosting Ray dashboards. Ray dashboards, by default, run on all network interfaces,
    which can expose them to the public internet if no other protective mechanisms
    are in place on the system.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0023
  target: AML.T0010.003
  relationship-type: employs
  description: HuggingFace tokens could allow the adversary to replace the victim
    organization's models with malicious variants.
  tactic: AML.TA0004
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0023
  target: AML.T0025
  relationship-type: employs
  description: 'AI artifacts, credentials, and other valuable information can be exfiltrated
    via cyber means.


    The researchers found evidence of reverse shells on vulnerable clusters. They
    can be used to maintain persistence, continue to run arbitrary code, and exfiltrate.'
  tactic: AML.TA0010
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0023
  target: AML.T0035
  relationship-type: employs
  description: 'Adversaries could collect AI artifacts including production models
    and data.


    The researchers observed running production workloads from several organizations
    from a variety of industries.'
  tactic: AML.TA0009
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0023
  target: AML.T0048.000
  relationship-type: employs
  description: Adversaries can cause financial harm to the victim organization. Exfiltrated
    credentials could be used to deplete credits or drain accounts. The GPU cloud
    resources themselves are costly. The researchers found evidence of cryptocurrency
    miners on vulnerable Ray clusters.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
- source: AML.CS0023
  target: AML.T0049
  relationship-type: employs
  description: Once open Ray clusters have been identified, adversaries could use
    the Jobs API to invoke jobs onto accessible clusters. The Jobs API does not support
    any kind of authorization, so anyone with network access to the cluster can execute
    arbitrary code remotely.
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0023
  target: AML.T0055
  relationship-type: employs
  description: 'The attackers could collect unsecured credentials stored in the cluster.


    The researchers observed SSH keys, OpenAI tokens, HuggingFace tokens, Stripe tokens,
    cloud environment keys (AWS, GCP, Azure, Lambda Labs), Kubernetes secrets.'
  tactic: AML.TA0013
  step-id: S03
  leads-to:
  - S04
```

## Structured source fields

```yaml
name: ShadowRay
references:
- id: anyscale
  title: Anyscale Update on CVEs
  url: https://www.anyscale.com/blog/update-on-ray-cves-cve-2023-6019-cve-2023-6020-cve-2023-6021-cve-2023-48022-cve-2023-48023
- id: nvd
  title: CVE-2023-48022
  url: https://nvd.nist.gov/vuln/detail/CVE-2023-48022
- id: oligo
  title: 'ShadowRay: First Known Attack Campaign Targeting AI Workloads Actively Exploited
    In The Wild'
  url: https://www.oligo.security/blog/shadowray-attack-ai-workloads-actively-exploited-in-the-wild
- id: protectai
  title: 'ShadowRay: AI Infrastructure Is Being Exploited In the Wild'
  url: https://protectai.com/threat-research/shadowray-ai-infrastructure-is-being-exploited-in-the-wild
created-date: '2025-03-14'
modified-date: '2025-03-14'
type: Incident
actor: Ray
target: Multiple systems
reporter: Oligo Research Team
date: '2023-09-05'
date-granularity: Day
id: AML.CS0023
uuid: 9e53f541-40c8-53c1-a5e4-4188a074f2fc
object-type: case-study
```
