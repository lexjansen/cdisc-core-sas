# cdisc-core-sas

The [cdisc-core-sas GitHub repository](https://github.com/lexjansen/cdisc-core-sas) contains working files and other artefacts to support a Proof of Concept for running CDISC CORE within SAS.

This Proof of Concepts is based on CORE release v0.9.3 (March 31, 2025) and was developed on Windows 10 with SAS 9.4 TS1M7.

## Supported python versions

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100)

## Installing dependencies

These steps should be run before running the SAS programs.

- Create a local copy of the lexjansen/cdisc-core-sas GitHub repo:

  `git clone https://github.com/lexjansen/cdisc-core-sas.git`

- Create a virtual environment in your copy of the lexjansen/cdisc-core-sas repo:

  `python -m venv <virtual_environment_name>`
- Activate the virtual environment:

  `.\<virtual_environment_name>\Scripts\Activate` -- on windows

- Install the requirements.

`python -m pip install -r requirements.txt` # From the root directory

## Environment variables

Define the following OS environment variables:

- `CORE_PATH` - Location of the local cdisc-rules-engine local repo clone
- `CDISC_LIBRARY_API_KEY` - CDISC Library API Key for updating the rules cache

Alternatively, the CDISC_LIBRARY_API_KEY variable can be set in `programs/options.sas` or in the `core_update_cache` macro call.

## Run SAS programs

Check the options in `programs/options.sas` to be able to run Python:

```SAS
options set = MAS_PYPATH = "&project_folder/.venv/Scripts/python.exe";
options set = MAS_M2PATH = "%sysget(SASROOT)/tkmas/sasmisc/mas2py.py";
```

Run the following SAS programs (make sure to update the `project_folder` macro variable in each program):

- programs/create_core_functions.sas (creates the `core_funcs` dataset in `macros`)
- programs/run_core_update_cache.sas (updates the cache in `resources\cache`)

After this all the other SAS programs can run:

- `programs/run_core_list_ct.sas`
- `programs/run_core_list_dataset_metadata.sas`
- `programs/run_core_list_rules.sas`
- `programs/run_core_list_rule_sets.sas`
- `programs/run_core_validate_data.sas`
- `programs/run_core_validate_data_select.sas`
- `programs/run_core_validate_data_local.sas`
- `programs/run_core_validate_data_json.sas`
- `programs/run_core_validate_data_ndjson.sas`

## Documentation

  The [doc](https://github.com/lexjansen/cdisc-core-sas/tree/main/doc) folder contains documentation: [Running the CDISC Open Rules Engine (CORE) in BASE SAS©](doc/SD-044.pdf)

## Issues

When encountering issues, please open an issue at [https://github.com/lexjansen/cdisc-core-sas/issues](https://github.com/lexjansen/cdisc-core-sas/issues).

## License

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
This project is using the [MIT](http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative") license (see [`LICENSE`](LICENSE)).

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
The CDISC CORE Engine is licensed under the [MIT](http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative") license (see [`LICENSE`](LICENSE-CDISC_RULES_ENGINE)).
