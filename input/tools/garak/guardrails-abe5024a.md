---
title: Guardrails
source: NVIDIA garak
source_type: official_tool_documentation
published_at: '2026-07-18'
security_domain: llm_vulnerability_evaluation
trust_level: official_project
canonical_url: https://github.com/NVIDIA/garak/blob/main/docs/source/generators/guardrails.rst
document_version: archive-sha256:5aede97786a760811142cb0d57671266c259297da9d1a983f8507b13a6dba134
license: Apache-2.0
source_path: docs/source/generators/guardrails.rst
---

# Guardrails

```text
garak.generators.guardrails
===========================

This is a generator for warpping a NeMo Guardrails configuration. Using this
garak generator enables security testing of a Guardrails config.

The ``guardrails`` generator expects a path to a valid Guardrails configuration
to be passed as its name. For example,

.. code-block::

   garak -t guardrails -n sample_abc/config

This generator requires installation of the `guardrails <https://pypi.org/project/nemoguardrails/>`_
Python package.

When invoked, garak sends prompts in series to the Guardrails setup using
``rails.generate``, and waits for a response. The generator does not support
parallisation, so it's recommended to run smaller probes, or set ``generations``
to a low value, in order to reduce garak run time.

.. automodule:: garak.generators.guardrails
   :members:
   :undoc-members:
   :show-inheritance:
```
