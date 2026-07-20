---
title: Arbitrary Code Execution with Google Colab
source: MITRE ATLAS
source_type: authoritative_framework
published_at: '2025-03-14'
security_domain: adversarial_ml
trust_level: authoritative
canonical_url: https://atlas.mitre.org/studies/AML.CS0018
document_version: '2026.06'
license: Apache-2.0
source_id: AML.CS0018
object_type: case-study
---

# AML.CS0018: Arbitrary Code Execution with Google Colab

## Description

Google Colab is a Jupyter Notebook service that executes on virtual machines.  Jupyter Notebooks are often used for ML and data science research and experimentation, containing executable snippets of Python code and common Unix command-line functionality.  In addition to data manipulation and visualization, this code execution functionality can allow users to download arbitrary files from the internet, manipulate files on the virtual machine, and so on.

Users can also share Jupyter Notebooks with other users via links.  In the case of notebooks with malicious code, users may unknowingly execute the offending code, which may be obfuscated or hidden in a downloaded script, for example.

When a user opens a shared Jupyter Notebook in Colab, they are asked whether they'd like to allow the notebook to access their Google Drive.  While there can be legitimate reasons for allowing Google Drive access, such as to allow a user to substitute their own files, there can also be malicious effects such as data exfiltration or opening a server to the victim's Google Drive.

This exercise raises awareness of the effects of arbitrary code execution and Colab's Google Drive integration.  Practice secure evaluations of shared Colab notebook links and examine code prior to execution.

## Explicit ATLAS relationships

```yaml
- source: AML.CS0018
  target: AML.T0010.001
  relationship-type: employs
  description: 'Jupyter notebooks are often used for ML and data science research
    and experimentation, containing executable snippets of Python code and common
    Unix command-line functionality.

    Users may come across a compromised notebook on public websites or through direct
    sharing.'
  tactic: AML.TA0004
  step-id: S01
  leads-to:
  - S02
- source: AML.CS0018
  target: AML.T0011
  relationship-type: employs
  description: A victim user may unwittingly execute malicious code provided as part
    of a compromised Colab notebook.  Malicious code can be obfuscated or hidden in
    other files that the notebook downloads.
  tactic: AML.TA0005
  step-id: S03
  leads-to:
  - S04
- source: AML.CS0018
  target: AML.T0012
  relationship-type: employs
  description: 'A victim user may mount their Google Drive into the compromised Colab
    notebook.  Typical reasons to connect machine learning notebooks to Google Drive
    include the ability to train on data stored there or to save model output files.


    ```

    from google.colab import drive

    drive.mount(''''/content/drive'''')

    ```


    Upon execution, a popup appears to confirm access and warn about potential data
    access:


    > This notebook is requesting access to your Google Drive files. Granting access
    to Google Drive will permit code executed in the notebook to modify files in your
    Google Drive. Make sure to review notebook code prior to allowing this access.


    A victim user may nonetheless accept the popup and allow the compromised Colab
    notebook access to the victim''''s Drive.  Permissions granted include:

    - Create, edit, and delete access for all Google Drive files

    - View Google Photos data

    - View Google contacts'
  tactic: AML.TA0004
  step-id: S02
  leads-to:
  - S03
- source: AML.CS0018
  target: AML.T0017
  relationship-type: employs
  description: An adversary creates a Jupyter notebook containing obfuscated, malicious
    code.
  tactic: AML.TA0003
  step-id: S00
  leads-to:
  - S01
- source: AML.CS0018
  target: AML.T0025
  relationship-type: employs
  description: 'As a result of Google Drive access, the adversary may open a server
    to exfiltrate private data or ML model artifacts.


    An example from the referenced article shows the download, installation, and usage
    of `ngrok`, a server application, to open an adversary-accessible URL to the victim''s
    Google Drive and all its files.'
  tactic: AML.TA0010
  step-id: S05
  leads-to:
  - S06
- source: AML.CS0018
  target: AML.T0035
  relationship-type: employs
  description: 'Adversary may search the victim system to find private and proprietary
    data, including ML model artifacts.  Jupyter Notebooks [allow execution of shell
    commands](https://colab.research.google.com/github/jakevdp/PythonDataScienceHandbook/blob/master/notebooks/01.05-IPython-And-Shell-Commands.ipynb).


    This example searches the mounted Drive for PyTorch model checkpoint files:


    ```

    !find /content/drive/MyDrive/ -type f -name *.pt

    ```

    > /content/drive/MyDrive/models/checkpoint.pt'
  tactic: AML.TA0009
  step-id: S04
  leads-to:
  - S05
- source: AML.CS0018
  target: AML.T0048
  relationship-type: employs
  description: Exfiltrated data may include sensitive or private data such as proprietary
    data stored in Google Drive, as well as user contacts and photos.  As a result,
    the user may be harmed financially, reputationally, and more.
  tactic: AML.TA0011
  step-id: S07
  leads-to: []
- source: AML.CS0018
  target: AML.T0048.004
  relationship-type: employs
  description: Exfiltrated data may include sensitive or private data such as ML model
    artifacts stored in Google Drive.
  tactic: AML.TA0011
  step-id: S06
  leads-to:
  - S07
```

## Structured source fields

```yaml
name: Arbitrary Code Execution with Google Colab
references:
- id: ref-1
  title: Be careful who you colab with
  url: https://medium.com/mlearning-ai/careful-who-you-colab-with-fa8001f933e7
created-date: '2023-10-30'
modified-date: '2025-03-14'
type: Exercise
actor: Tony Piazza
target: Google Colab
date: '2022-07-01'
date-granularity: Month
id: AML.CS0018
uuid: 87a57b01-6f54-527e-9519-9dd5711fc820
object-type: case-study
```
