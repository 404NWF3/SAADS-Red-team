---
title: Index Detectors
source: NVIDIA garak
source_type: official_tool_documentation
published_at: '2026-07-18'
security_domain: llm_vulnerability_evaluation
trust_level: official_project
canonical_url: https://github.com/NVIDIA/garak/blob/main/docs/source/index_detectors.rst
document_version: archive-sha256:5aede97786a760811142cb0d57671266c259297da9d1a983f8507b13a6dba134
license: Apache-2.0
source_path: docs/source/index_detectors.rst
---

# Index Detectors

```text
Detectors
=========


Detectors classify responses into two categories:

- **hit**: A response exhibiting the failure mode the detector identifies (e.g., jailbreak successful, unsafe content generated)
- **pass**: A response that does not exhibit the target failure mode (e.g., request refused, safety maintained)

For detailed information on detector metrics and evaluation, see :doc:`../detector_metrics`.


.. toctree::
   :maxdepth: 2

   detectors/base
   detectors/agent_breaker
   detectors/always
   detectors/any
   detectors/ansiescape
   detectors/apikey
   detectors/continuation
   detectors/dan
   detectors/divergence
   detectors/encoding
   detectors/exploitation
   detectors/fileformats
   detectors/goodside
   detectors/judge
   detectors/knownbadsignatures
   detectors/leakreplay
   detectors/lmrc
   detectors/malwaregen
   detectors/misleading
   detectors/mitigation
   detectors/packagehallucination
   detectors/perspective
   detectors/promptinject
   detectors/productkey
   detectors/propile
   detectors/shields
   detectors/snowball
   detectors/sysprompt_extraction
   detectors/unsafe_content
   detectors/visual_jailbreak
   detectors/web_injection
```
