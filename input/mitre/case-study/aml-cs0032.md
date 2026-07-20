---
title: Attempted Evasion of ML Phishing Webpage Detection System
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-09-29'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0032
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0032
object_type: case-study
---

# AML.CS0032: Attempted Evasion of ML Phishing Webpage Detection System

## Description

Adversaries create phishing websites that appear visually similar to legitimate sites. These sites are designed to trick users into entering their credentials, which are then sent to the bad actor. To combat this behavior, security companies utilize AI/ML-based approaches to detect phishing sites and block them in their endpoint security products.

In this incident, adversarial examples were identified in the logs of a commercial machine learning phishing website detection system. The detection system makes an automated block/allow determination from the "phishing score" of an ensemble of image classifiers each responsible for different phishing indicators (visual similarity, input form detection, etc.). The adversarial examples appeared to employ several simple yet effective strategies for manually modifying brand logos in an attempt to evade image classification models. The phishing websites which employed logo modification methods successfully evaded the model responsible detecting brand impersonation via visual similarity. However, the other components of the system successfully flagged the phishing websites.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0032
  target: AML.T0015
  relationship-type: employs
  description: The visual similarity model used to detect brand impersonation was
    evaded. However, other components of the phishing detection system successfully
    identified the phishing websites.
  tactic: AML.TA0007
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0032
  target: AML.T0043.003
  relationship-type: employs
  description: 'Several cheap, yet effective strategies for manually modifying logos
    were observed:

    | Evasive Strategy | Count |

    | - | - |

    | Company name style | 25 |

    | Blurry logo | 23 |

    | Cropping | 20 |

    | No company name | 16 |

    | No visual logo | 13 |

    | Different visual logo | 12 |

    | Logo stretching | 11 |

    | Multiple forms - images | 10 |

    | Background patterns | 8 |

    | Login obfuscation | 6 |

    | Masking | 3 |'
  tactic: AML.TA0001
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0032
  target: AML.T0048.003
  relationship-type: employs
  description: The end user may experience a variety of harms including financial
    and privacy harms depending on the credentials stolen by the adversary.
  tactic: AML.TA0011
  step-id: S03
  leads-to: []
- source: AML.CS0032
  target: AML.T0052
  relationship-type: employs
  description: If the adversary can successfully evade detection, they can continue
    to operate their phishing websites and steal the victim's credentials.
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
```

## Structured source fields

```yaml
name: Attempted Evasion of ML Phishing Webpage Detection System
references:
- id: ref-1
  title: '"Real Attackers Don''t Compute Gradients": Bridging the Gap Between Adversarial
    ML Research and Practice'
  url: https://arxiv.org/abs/2212.14315
- id: ref-2
  title: Real Attackers Don't Compute Gradients Supplementary Resources
  url: https://real-gradients.github.io/
created-date: '2025-09-29'
modified-date: '2025-09-29'
type: Incident
actor: Unknown
target: Commercial ML Phishing Webpage Detector
reporter: Norton Research Group (NRG)
date: '2022-12-01'
date-granularity: Month
id: AML.CS0032
uuid: 7338b54f-7731-53dc-abf2-fa5a045020b0
object-type: case-study
```
