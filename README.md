### Supported python versions

[![Python 3.9](https://img.shields.io/badge/python-3.9-green.svg)](https://www.python.org/downloads/release/python-390)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-310)

# cdisc-core-sas

Proof of Concept for running CDISC CORE within SAS

### Installing dependencies

These steps should be run before running the SAS programs.

- Create a local copy of the cdisc-rules-engine GitHub repo:

  `git clone https://github.com/lexjansen/cdisc-core-sas.git`

- Create a virtual environment in your copy of the cdisc-core-sas repo:

  `python -m venv <virtual_environment_name>`
- Activate the virtual environment:

  `./<virtual_environment_name>/bin/activate` -- on linux/mac </br>
  `.\<virtual_environment_name>\Scripts\Activate` -- on windows

- Install the requirements.

`python -m pip install -r <location of cdisc-rules-engine local repo clone>/requirements.txt` # From the root directory

### Environment variables

Define the following environment variables:

- CORE_PATH - Location of the local cdisc-rules-engine local repo clone
- CDISC_LIBRARY_API_KEY - CDISC Library API Key for updating the rules cache
