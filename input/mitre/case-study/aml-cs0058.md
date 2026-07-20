---
title: Google Photos AI Model Extraction
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2026-06-30'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0058
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0058
object_type: case-study
---

# AML.CS0058: Google Photos AI Model Extraction

## Description

Skyld researchers analyzed the Google Photos Android application and recovered TensorFlow Lite models used by AI-powered photo editing and image analysis features. The researchers found models stored unencrypted in the application's assets, embedded in the native library, and encrypted on disk. They used static reverse engineering to locate TFLite artifacts and dynamic instrumentation with Frida to capture encrypted models after runtime decryption. The recovered models provided white-box access to proprietary Google Photos model artifacts.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0058
  target: AML.T0007
  relationship-type: employs
  description: Skyld researchers analyzed the Google Photos Android Package (APK)
    and identified TensorFlow Lite as the machine learning framework used by the app.
    They searched the application package and native libraries for TFLite artifacts
    using the TFL3 file identifier.
  tactic: AML.TA0008
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0058
  target: AML.T0015
  relationship-type: employs
  description: Adversarial data could be used to evade or otherwise degrade the Google
    Photos models including face and object detection.
  tactic: AML.TA0011
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0058
  target: AML.T0025
  relationship-type: employs
  description: The researchers used static analysis and Frida instrumentation to recover
    model files. For encrypted models, they intercepted decrypted TFLite files during
    runtime as Google Photos loaded them for execution.
  tactic: AML.TA0010
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0058
  target: AML.T0035
  relationship-type: employs
  description: The researchers collected TensorFlow Lite model artifacts from multiple
    locations in the APK, including unencrypted assets, files embedded in the native
    library, and application-specific folders.
  tactic: AML.TA0009
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0058
  target: AML.T0043.000
  relationship-type: employs
  description: The recovered TensorFlow Lite models could enable white-box adversarial
    example generation.
  tactic: AML.TA0001
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0058
  target: AML.T0044
  relationship-type: employs
  description: Exfiltrating model files from the APK gave the researchers full access
    to the Google Photos AI models, including those used for tasks such as face detection,
    object detection, segmentation, depth estimation, image quality assessment, and
    blur detection.
  tactic: AML.TA0000
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0058
  target: AML.T0048.004
  relationship-type: employs
  description: The recovered models represented proprietary Google Photos AI assets.
    An adversary or competitor could use the extracted models to study, reuse, or
    replicate Google Photos capabilities, reducing the cost of independently developing
    similar features.
  tactic: AML.TA0011
  step-id: S06
  leads-to: []
```

## Structured source fields

```yaml
name: Google Photos AI Model Extraction
references:
- id: skyld-google-photos-model-extraction
  title: 'Google Photos AI Models: The Secret Sauce That Can Be Stolen'
  url: https://skyld.io/google-photos-model-extraction
created-date: '2026-06-30'
modified-date: '2026-06-30'
type: Exercise
actor: Skyld
target: Google Photos Android App
date: '2025-03-01'
date-granularity: Month
id: AML.CS0058
uuid: 7476ef00-330a-58d2-b3d4-47922d4da55f
object-type: case-study
```
