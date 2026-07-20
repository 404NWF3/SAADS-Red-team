---
title: Backdoor Attack on Deep Learning Models in Mobile Apps
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0013
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0013
object_type: case-study
---

# AML.CS0013: Backdoor Attack on Deep Learning Models in Mobile Apps

## Description

Deep learning models are increasingly used in mobile applications as critical components.
Researchers from Microsoft Research demonstrated that many deep learning models deployed in mobile apps are vulnerable to backdoor attacks via "neural payload injection."
They conducted an empirical study on real-world mobile deep learning apps collected from Google Play. They identified 54 apps that were vulnerable to attack, including popular security and safety critical applications used for cash recognition, parental control, face authentication, and financial services.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0013
  target: AML.T0002.001
  relationship-type: employs
  description: 'The researchers acquired the apps'' APKs from the Google Play store.

    They filtered the list of potential target applications by searching the code
    metadata for keywords related to TensorFlow or TFLite and their model binary formats
    (.tf and .tflite).

    The models were extracted from the APKs using Apktool.'
  tactic: AML.TA0003
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0013
  target: AML.T0004
  relationship-type: employs
  description: To identify a list of potential target models, the researchers searched
    the Google Play store for apps that may contain embedded deep learning models
    by searching for deep learning related keywords.
  tactic: AML.TA0002
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0013
  target: AML.T0010.003
  relationship-type: employs
  description: In practice, the malicious APK would need to be installed on victim's
    devices via a supply chain compromise.
  tactic: AML.TA0004
  step-id: S06
  leads-to:
  - S07
- source: AML.CS0013
  target: AML.T0015
  relationship-type: employs
  description: 'Presenting the visual trigger causes the victim model to be bypassed.

    The researchers demonstrated this can be used to evade ML models in

    several safety-critical apps in the Google Play store.'
  tactic: AML.TA0011
  step-id: S09
  leads-to: []
- source: AML.CS0013
  target: AML.T0017.000
  relationship-type: employs
  description: 'The researchers developed a novel approach to insert a backdoor into
    a compiled model that can be activated with a visual trigger.  They inject a "neural
    payload" into the model that consists of a trigger detection network and conditional
    logic.

    The trigger detector is trained to detect a visual trigger that will be placed
    in the real world.

    The conditional logic allows the researchers to bypass the victim model when the
    trigger is detected and provide model outputs of their choosing.

    The only requirements for training a trigger detector are a general

    dataset from the same modality as the target model (e.g. ImageNet for image classification)
    and several photos of the desired trigger.'
  tactic: AML.TA0003
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0013
  target: AML.T0018.001
  relationship-type: employs
  description: 'The researchers poisoned the victim model by injecting the neural

    payload into the compiled models by directly modifying the computation

    graph.

    The researchers then repackage the poisoned model back into the APK'
  tactic: AML.TA0006
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0013
  target: AML.T0041
  relationship-type: employs
  description: At inference time, only physical environment access is required to
    trigger the attack.
  tactic: AML.TA0000
  step-id: S08
  leads-to:
  - S09
- source: AML.CS0013
  target: AML.T0042
  relationship-type: employs
  description: To verify the success of the attack, the researchers confirmed the
    app did not crash with the malicious model in place, and that the trigger detector
    successfully detects the trigger.
  tactic: AML.TA0001
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0013
  target: AML.T0043.004
  relationship-type: employs
  description: The trigger is placed in the physical environment, where it is captured
    by the victim's device camera and processed by the backdoored ML model.
  tactic: AML.TA0001
  step-id: S07
  leads-to:
  - S08
- source: AML.CS0013
  target: AML.T0044
  relationship-type: employs
  description: This provided the researchers with full access to the ML model, albeit
    in compiled, binary form.
  tactic: AML.TA0000
  step-id: S02
  leads-to:
  - S03
```

## Structured source fields

```yaml
name: Backdoor Attack on Deep Learning Models in Mobile Apps
references:
- id: ref-1
  title: 'DeepPayload: Black-box Backdoor Attack on Deep Learning Models through Neural
    Payload Injection'
  url: https://arxiv.org/abs/2101.06896
created-date: '2022-02-03'
modified-date: '2025-03-14'
type: Exercise
actor: Yuanchun Li, Jiayi Hua, Haoyu Wang, Chunyang Chen, Yunxin Liu
target: ML-based Android Apps
date: '2021-01-18'
date-granularity: Day
id: AML.CS0013
uuid: 3fe7831d-6f56-57d6-8140-7e5f32da53d7
object-type: case-study
```
