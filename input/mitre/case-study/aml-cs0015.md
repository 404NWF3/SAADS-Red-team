---
title: Compromised PyTorch Dependency Chain
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0015
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0015
object_type: case-study
---

# AML.CS0015: Compromised PyTorch Dependency Chain

## Description

Linux packages for PyTorch's pre-release version, called Pytorch-nightly, were compromised from December 25 to 30, 2022 by a malicious binary uploaded to the Python Package Index (PyPI) code repository.  The malicious binary had the same name as a PyTorch dependency and the PyPI package manager (pip) installed this malicious package instead of the legitimate one.

This supply chain attack, also known as "dependency confusion," exposed sensitive information of Linux machines with the affected pip-installed versions of PyTorch-nightly. On December 30, 2022, PyTorch announced the incident and initial steps towards mitigation, including the rename and removal of `torchtriton` dependencies.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0015
  target: AML.T0010.001
  relationship-type: employs
  description: 'A malicious dependency package named `torchtriton` was uploaded to
    the PyPI code repository with the same package name as a package shipped with
    the PyTorch-nightly build. This malicious package contained additional code that
    uploads sensitive data from the machine.

    The malicious `torchtriton` package was installed instead of the legitimate one
    because PyPI is prioritized over other sources. See more details at [this GitHub
    issue](https://github.com/pypa/pip/issues/8606).'
  tactic: AML.TA0004
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0015
  target: AML.T0025
  relationship-type: employs
  description: All gathered information, including file contents, is uploaded via
    encrypted DNS queries to the domain `*[dot]h4ck[dot]cfd`, using the DNS server
    `wheezy[dot]io`.
  tactic: AML.TA0010
  step-id: S02
  leads-to: []
- source: AML.CS0015
  target: AML.T0037
  relationship-type: employs
  description: 'The malicious package surveys the affected system for basic fingerprinting
    info (such as IP address, username, and current working directory), and steals
    further sensitive data, including:

    - nameservers from `/etc/resolv.conf`

    - hostname from `gethostname()`

    - current username from `getlogin()`

    - current working directory name from `getcwd()`

    - environment variables

    - `/etc/hosts`

    - `/etc/passwd`

    - the first 1000 files in the user''s `$HOME` directory

    - `$HOME/.gitconfig`

    - `$HOME/.ssh/*.`'
  tactic: AML.TA0009
  step-id: S01
  leads-to:
  - S02
```

## Structured source fields

```yaml
name: Compromised PyTorch Dependency Chain
references:
- id: ref-1
  title: PyTorch statement on compromised dependency
  url: https://pytorch.org/blog/compromised-nightly-dependency/
- id: ref-2
  title: Analysis by BleepingComputer
  url: https://www.bleepingcomputer.com/news/security/pytorch-discloses-malicious-dependency-chain-compromise-over-holidays/
created-date: '2022-02-03'
modified-date: '2025-03-14'
type: Incident
actor: Unknown
target: PyTorch
reporter: PyTorch
date: '2022-12-25'
date-granularity: Day
id: AML.CS0015
uuid: 3a415844-66be-5509-abd8-534252474926
object-type: case-study
```
