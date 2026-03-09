#!/usr/bin/env python3
"""
CLI entrypoint for the CDISC Rules Engine.
"""

import asyncio
import codecs
import json
import logging
import os
import pickle
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from cdisc_rules_engine.config import config
from cdisc_rules_engine.enums.dataformat_types import DataFormatTypes
from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
from cdisc_rules_engine.enums.progress_parameter_options import ProgressParameterOptions
from cdisc_rules_engine.enums.report_types import ReportTypes
from cdisc_rules_engine.models.external_dictionaries_container import (
    DictionaryTypes,
    ExternalDictionariesContainer,
)
from cdisc_rules_engine.models.validation_args import Validation_args
from cdisc_rules_engine.services.cache.cache_populator_service import CachePopulator
from cdisc_rules_engine.services.cache.cache_service_factory import CacheServiceFactory
from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService
from cdisc_rules_engine.utilities.utils import (
    generate_report_filename,
    get_rules_cache_key,
    # validate_dataset_files_exist,
)
from cdisc_rules_engine.constants import VALIDATION_FORMATS_MESSAGE, DEFAULT_ENCODING
from scripts.list_dataset_metadata_handler import list_dataset_metadata_handler
from scripts.run_validation import run_validation
from version import __version__

DEFAULT_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), DefaultFilePaths.CACHE.value
)


def validate_encoding(param, value):
    if value is None:
        return DEFAULT_ENCODING
    try:
        codecs.lookup(value)
        return value
    except LookupError:
        raise ValueError(
            f"Invalid encoding '{value}'. Please provide a valid encoding name "
            f"(e.g., utf-8, utf-16, utf-32, cp1252, latin-1)."
        )


def valid_data_file(data_path: list) -> tuple[list, set]:
    allowed_formats = [
        DataFormatTypes.XPT.value,
        DataFormatTypes.JSON.value,
        DataFormatTypes.NDJSON.value,
        DataFormatTypes.XLSX.value,
    ]
    found_formats = set()
    file_list = []
    ignored_files = []

    for file in data_path:
        file_extension = os.path.splitext(file)[1][1:].upper()
        if file_extension in allowed_formats:
            found_formats.add(file_extension)
            file_list.append(file)
        elif file_extension:
            ignored_files.append(os.path.basename(file))

    if ignored_files:
        logger = logging.getLogger("validator")
        logger.warning(
            f"Ignoring {len(ignored_files)} file(s) with unsupported formats: {', '.join(ignored_files[:5])}"
            + ("..." if len(ignored_files) > 5 else "")
        )

    if DataFormatTypes.XLSX.value in found_formats:
        if len(found_formats) > 1:
            return [], found_formats
        elif len(file_list) > 1:
            return [], found_formats
        else:
            return file_list, found_formats
    if len(found_formats) >= 1:
        return file_list, found_formats
    else:
        return [], set()


def _validate_data_directory(
    data: str, logger, filetype: str = None
) -> tuple[list, set]:
    """Validate data directory and return dataset paths and found formats."""
    # Added filetype argument to filter files by extension if provided
    if filetype:
        pattern = f"*.{filetype}"
        dataset_paths, found_formats = valid_data_file(
            [str(p) for p in Path(data).rglob(pattern) if p.is_file()]
        )
    else:
        dataset_paths, found_formats = valid_data_file(
            [str(p) for p in Path(data).rglob("*") if p.is_file()]
        )

    if DataFormatTypes.XLSX.value in found_formats and len(found_formats) > 1:
        logger.error(
            f"Argument --data contains XLSX files mixed with other formats ({', '.join(found_formats)}).\n"
            f"Excel format (XLSX) validation only supports single files.\n"
            f"Please provide either a single XLSX file or use other supported formats: "
            f"{VALIDATION_FORMATS_MESSAGE}"
        )
        return [], set()

    if not dataset_paths:
        if DataFormatTypes.XLSX.value in found_formats and len(found_formats) == 1:
            logger.error(
                f"Multiple XLSX files found in directory: {data}\n"
                f"Excel format (XLSX) validation only supports single files.\n"
                f"Please provide either a single XLSX file or use other supported formats: "
                f"{VALIDATION_FORMATS_MESSAGE}"
            )
        else:
            logger.error(
                f"No valid dataset files found in directory: {data}\n"
                f"Supported formats: {VALIDATION_FORMATS_MESSAGE}\n"
                f"Please ensure your directory contains files in one of these formats."
            )
        return [], set()

    return dataset_paths, found_formats


def _validate_dataset_paths(dataset_path: tuple[str], logger) -> tuple[list, set]:
    """Validate dataset paths and return dataset paths and found formats."""
    dataset_paths, found_formats = valid_data_file([dp for dp in dataset_path])

    if DataFormatTypes.XLSX.value in found_formats and len(found_formats) > 1:
        logger.error(
            f"Argument --dataset-path contains XLSX files mixed with other formats ({', '.join(found_formats)}).\n"
            f"Excel format (XLSX) validation only supports single files.\n"
            f"Please provide either a single XLSX file or use other supported formats: "
            f"{VALIDATION_FORMATS_MESSAGE}"
        )
        return [], set()

    if not dataset_paths:
        if DataFormatTypes.XLSX.value in found_formats and len(found_formats) == 1:
            logger.error(
                f"Multiple XLSX files provided.\n"
                f"Excel format (XLSX) validation only supports single files.\n"
                f"Please provide either a single XLSX file or use other supported formats: "
                f"{VALIDATION_FORMATS_MESSAGE}"
            )
        else:
            logger.error(
                f"No valid dataset files provided.\n"
                f"Supported formats: {VALIDATION_FORMATS_MESSAGE}\n"
                f"Please ensure your files are in one of these formats."
            )
        return [], set()

    return dataset_paths, found_formats


def _validate_no_arguments(logger) -> None:
    """Validate that at least one dataset argument is provided."""
    logger.error("You must pass one of the following arguments: --dataset-path, --data")


def validate(
    standard: str = '',
    version: str = '',
    substandard: str = '',
    use_case: str = '',
    cache: str = DEFAULT_CACHE_PATH,
    pool_size: int = 10,
    log_level: str = 'disabled',
    data: str = '',
    filetype: str = '',
    dataset_path: tuple[str] = [],
    report_template: str = DefaultFilePaths.EXCEL_TEMPLATE_FILE.value,
    output_format: tuple[str] = [ReportTypes.XLSX.value],
    raw_report: bool = False,
    output: str = generate_report_filename(datetime.now().isoformat()),
    controlled_terminology_package: tuple[str] = [],
    define_version: str = '',
    rules: tuple[str] = [],
    exclude_rules: tuple[str] = [],
    local_rules: str = '',
    custom_standard: bool = False,
    define_xml_path: str = '',
    validate_xml: str = 'y',
    jsonata_custom_functions: tuple[str] = [],
    whodrug: str = '',
    meddra: str = '',
    loinc: str = '',
    medrt: str = '',
    unii: str = '',
    snomed_version: str = '',
    snomed_edition: str = '',
    snomed_url: str = 'https://snowstorm.snomedtools.org/snowstorm/snomed-ct/',
    progress: str = 'disabled',
    max_report_rows: int = 10000,
    max_errors_per_rule: tuple[int, bool] = (0, False),
    encoding: str = 'utf-8',
):
    """
    Validate data using CDISC Rules Engine

    Example:

    python core.py -s SDTM -v 3.4 -d /path/to/datasets
    """

    # Validate conditional options
    logger = logging.getLogger("validator")
    load_dotenv()
    #  validate_dataset_files_exist(dataset_path, logger)

    if not custom_standard:
        standard = standard.lower()

    if raw_report is True:
        if not (len(output_format) == 1 and output_format[0] == ReportTypes.JSON.value):
            logger.error(
                "Flag --raw-report can be used only when --output-format is JSON"
            )
            return

    if exclude_rules and rules:
        logger.error("Cannot use both --rules and --exclude-rules flags together.")
        return

    cache_path: str = os.path.join(os.path.dirname(__file__), cache)

    if standard == "tig":
        if not substandard or not use_case:
            logger.error(
                "Standard 'tig' requires both --substandard and --use-case to be specified."
            )
            return

    # Construct ExternalDictionariesContainer:
    external_dictionaries = ExternalDictionariesContainer(
        {
            DictionaryTypes.UNII.value: unii,
            DictionaryTypes.MEDRT.value: medrt,
            DictionaryTypes.MEDDRA.value: meddra,
            DictionaryTypes.WHODRUG.value: whodrug,
            DictionaryTypes.LOINC.value: loinc,
            DictionaryTypes.SNOMED.value: {
                "edition": snomed_edition,
                "version": snomed_version,
                "base_url": snomed_url,
            },
        }
    )
    # Validate dataset arguments
    if data:
        if dataset_path:
            logger.error(
                "Argument --dataset-path cannot be used together with argument --data"
            )
            return
        dataset_paths, found_formats = _validate_data_directory(data, logger, filetype)
        if not dataset_paths:
            return
    elif dataset_path:
        dataset_paths, found_formats = _validate_dataset_paths(dataset_path, logger)
        if not dataset_paths:
            return
    else:
        _validate_no_arguments(logger)
        return

    validate_xml_bool = True if validate_xml.lower() in ("y", "yes") else False
    run_validation(
        Validation_args(
            cache_path,
            pool_size,
            dataset_paths,
            log_level,
            report_template,
            standard,
            version,
            substandard,
            use_case,
            set(controlled_terminology_package),
            output,
            set(output_format),
            raw_report,
            define_version,
            external_dictionaries,
            rules,
            exclude_rules,
            local_rules,
            custom_standard,
            progress,
            define_xml_path,
            validate_xml_bool,
            jsonata_custom_functions,
            max_report_rows,
            max_errors_per_rule,
            encoding,
        )
    )


def update_cache(
    apikey: str = os.environ["CDISC_LIBRARY_API_KEY"],
    cache_path: str = DEFAULT_CACHE_PATH,
    custom_rules_directory: str = '',
    custom_rule: str = '',
    remove_custom_rules: str = '',
    update_custom_rule: str = '',
    custom_standard: str = '',
    custom_standard_encoding: str = '',
    remove_custom_standard: str = ''
):
    cache = CacheServiceFactory(config).get_cache_service()
    # CDISC library service should log failed requests instead of failing the
    # cache update process
    library_service = CDISCLibraryService(apikey, cache, raise_on_error=False)
    update_rules_only = not apikey
    cache_populator = CachePopulator(
        cache,
        library_service,
        custom_rules_directory,
        custom_rule,
        remove_custom_rules,
        update_custom_rule,
        custom_standard,
        custom_standard_encoding,
        remove_custom_standard,
        cache_path,
        rules_only=update_rules_only,
    )

    if update_rules_only:
        logger = logging.getLogger("validator")
        logger.warning("API key was not provided. Only CORE rules will be updated.")

    if custom_rule or custom_rules_directory:
        cache_populator.add_custom_rules()
    elif remove_custom_rules:
        cache_populator.remove_custom_rules_from_cache()
    elif update_custom_rule:
        cache_populator.update_custom_rule_in_cache()
    elif custom_standard:
        cache_populator.add_custom_standard_to_cache()
    elif remove_custom_standard:
        cache_populator.remove_custom_standards_from_cache()
    else:
        asyncio.run(cache_populator.update_cache())

    print("Cache update complete")


def list_rules(
    standard: str,
    version: str,
    substandard: str,
    output: str,
    cache_path: str = DEFAULT_CACHE_PATH,
    custom_rules: bool = False,
    rule_id: str = '',
):
    # Load all rules
    if custom_rules:
        rules_file = DefaultFilePaths.CUSTOM_RULES_CACHE_FILE.value
        dict_file = DefaultFilePaths.CUSTOM_RULES_DICTIONARY.value
    else:
        rules_file = DefaultFilePaths.RULES_CACHE_FILE.value
        dict_file = DefaultFilePaths.RULES_DICTIONARY.value
    with open(os.path.join(cache_path, rules_file), "rb") as f:
        rules_data = pickle.load(f)
    with open(os.path.join(cache_path, dict_file), "rb") as f:
        rules_dict = pickle.load(f)
    rules = []
    if rule_id:
        for id in rule_id:
            if id in rules_data:
                rules.append(rules_data[id])
    elif standard and version:
        key_prefix = get_rules_cache_key(
            standard, version.replace(".", "-"), substandard
        )
        if key_prefix in rules_dict:
            rule_ids = rules_dict[key_prefix]
            for rid in rule_ids:
                if rid in rules_data:
                    rules.append(rules_data[rid])
    else:
        # Print all rules
        rules = list(rules_data.values())
    print(
        f"Found {len(rules)} rules for standard={standard}, version={version}, "
        f"substandard={substandard}, custom_rules={custom_rules}, rule_id={rule_id}"
    )
    with open(output, "w") as f:
        json.dump(rules, f, indent=4)


def list_rule_sets(
    output: str,
    cache_path: str = DefaultFilePaths.CACHE.value,
    custom: bool = False
):
    """Lists all standards and versions for which rules are available."""
    if custom:
        rules_file = DefaultFilePaths.CUSTOM_RULES_DICTIONARY.value
    else:
        rules_file = DefaultFilePaths.RULES_DICTIONARY.value
    with open(os.path.join(cache_path, rules_file), "rb") as f:
        rules_data = pickle.load(f)

    rule_sets = {}
    report_data = []
    for key in rules_data.keys():
        if "/" in key:
            parts = key.split("/")
            standard = parts[0]
            version = parts[1]
            substandard = parts[2] if len(parts) > 2 else None
            if standard not in rule_sets:
                rule_sets[standard] = set()
            rule_sets[standard].add((version, substandard))
    for standard in sorted(rule_sets.keys()):
        versions = sorted(rule_sets[standard], key=lambda x: (x[0], x[1] or ""))
        for version, substandard in versions:
            if substandard:
                print(f"{standard}, {version}, {substandard}")
                report_data.append(f"{standard}, {version}, {substandard}")
            else:
                print(f"{standard}, {version}")
                report_data.append(f"{standard}, {version}")

    with open(output, "w") as f:
        json.dump(report_data, f)


def list_dataset_metadata(
    dataset_path: tuple[str],
    output: str
):
    """
    Command that lists metadata of given datasets.

    Input:
        core.py list-ds-metadata -dp=path_1 -dp=path_2 -dp=path_3 ...
    Output:
        [
           {
              "domain":"AE",
              "filename":"ae.xpt",
              "full_path":"/Users/Aleksei_Furmenkov/PycharmProjects/cdisc-rules-engine/resources/data/ae.xpt",
              "file_size":"38000",
              "label":"Adverse Events",
              "modification_date":"2020-08-21T09:14:26"
           },
           {
              "domain":"EX",
              "filename":"ex.xpt",
              "full_path":"/Users/Aleksei_Furmenkov/PycharmProjects/cdisc-rules-engine/resources/data/ex.xpt",
              "file_size":"78050",
              "label":"Exposure",
              "modification_date":"2021-09-17T09:23:22"
           },
           ...
        ]
    """
    with open(output, "w") as f:
        json.dump(list_dataset_metadata_handler(dataset_path), f)


def version():
    print(__version__)


def list_ct(
    subsets: tuple[str],
    output: str,
    cache_path: str = DefaultFilePaths.CACHE.value
):
    """
    Command to list the ct packages available in the cache.
    """
    if subsets:
        subsets = set([subset.lower() for subset in subsets])
    ctset = []
    for file in os.listdir(cache_path):
        file_prefix = file[0 : file.find("ct-") + 2]
        if file_prefix.endswith("ct") and (not subsets or file_prefix in subsets):
            ct = os.path.splitext(file)[0]
            print(ct)
            ctset.append(ct)
    with open(output, "w") as f:
        json.dump(ctset, f)


def test_validate(filetype):
    """
    Verify CORE with a test validation.
    Requires FILETYPE argument: 'json' or 'xpt'.
    Report file is confirmed and automatically cleaned up. For actual validation, use 'validate' command.
    """
    try:
        base_path = os.path.join("resources", "datasets")
        if filetype.lower() == "json":
            test_file = os.path.join(base_path, "TS.json")
            output_name = "json_validation_output"
        else:
            test_file = os.path.join(base_path, "ae.xpt")
            output_name = "xpt_validation_output"
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"Test dataset not found: {test_file}")
        cache_path = DEFAULT_CACHE_PATH
        pool_size = 10
        log_level = "disabled"
        standard = "sdtmig"
        version = "3.4"
        output_format = {ReportTypes.XLSX.value}
        external_dictionaries = ExternalDictionariesContainer({})
        progress = ProgressParameterOptions.BAR.value
        max_report_errors = (0, False)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, output_name)
            run_validation(
                Validation_args(
                    cache_path,
                    pool_size,
                    [test_file],
                    log_level,
                    None,
                    standard,
                    version,
                    None,
                    None,
                    set(),
                    output,
                    output_format,
                    False,
                    None,
                    external_dictionaries,
                    [],
                    [],
                    None,
                    False,
                    progress,
                    None,
                    False,
                    (),
                    None,
                    max_report_errors,
                    None,
                )
            )
            print(f"{filetype.upper()} validation completed successfully!")
        sys.exit(0)
    except Exception as e:
        import traceback

        print(f"{filetype.upper()} validation test failed: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":

    version()

    # Update cache
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache'
    )

    # Add custom rules
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        custom_rules_directory='./testdata/rules'
    )

    # Update custom rule
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        update_custom_rule='./testdata/rules/CUSTOM-001.yml'
    )

    # Add custom standard
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        custom_standard='./testdata/standards/custom_standard.json'
    )

    # Remove custom rule
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        remove_custom_rules='CUSTOM-001'
    )

    # Remove custom rules
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        remove_custom_rules='ALL'
    )

    # Remove custom standard
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        remove_custom_standard=['mycustom/1-0']
    )

    # Add custom rules
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        custom_rules_directory='./testdata/rules'
    )

    # Add custom standard
    update_cache(
        apikey=os.environ.get("CDISC_LIBRARY_API_KEY"),
        cache_path='./resources/cache',
        custom_standard='./testdata/standards/custom_standard.json'
    )

    list_rule_sets(cache_path='./resources/cache', output="./json/core_rule_sets.json")
    list_rule_sets(cache_path='./resources/cache', output="./json/core_rule_sets_custom.json", custom=True)

    list_rules(
        cache_path='./resources/cache',
        output="./json/core_rules_sdtmig_33.json",
        standard='sdtmig',
        version='3-3',
        substandard=''
    )
    list_rules(
        cache_path='./resources/cache',
        output="./json/core_rules_sdtmig_34.json",
        standard='sdtmig',
        version='3-4',
        substandard=''
    )
    list_rules(
        cache_path='./resources/cache',
        output="./json/core_rules_adamig_10.json",
        standard='adamig',
        version='1-3',
        substandard=''
    )
    list_rules(
        cache_path='./resources/cache',
        output="./json/core_rules_sdtmig_32.json",
        standard='sdtmig',
        version='3-2',
        substandard=''
    )
    list_rules(
        cache_path='./resources/cache',
        output="./json/core_rules_mycustom_10.json",
        standard='mycustom',
        version='1-0',
        substandard='',
        custom_rules=True
    )

    list_ct(output="./json/core_ct.json", subsets=[])

    list_dataset_metadata(
        output="./json/core_dataset_metadata_xpt.json",
        dataset_path=[
            './testdata/sdtm/dm.xpt',
            './testdata/sdtm/ae.xpt',
            './testdata/sdtm/ex.xpt',
            './testdata/sdtm/lb.xpt'
        ]
    )

    list_dataset_metadata(
        output="./json/core_dataset_metadata_json.json",
        dataset_path=[
            './testdata/sdtm_json/dm.json',
            './testdata/sdtm_json/ae.json',
            './testdata/sdtm_json/ex.json',
            './testdata/sdtm_json/lb.json'
        ]
    )

    validate(
        standard='sdtmig',
        version='3-3',
        data='./testdata/sdtm',
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        progress='bar'
    )

    validate(
        standard='sdtmig',
        version='3-3',
        cache='./resources/cache',
        data='./testdata/sdtm',
        report_template='./resources/templates/report-template.xlsx',
        output_format=['JSON', 'XLSX'],
        raw_report=False,
        output='./reports/' + generate_report_filename(datetime.now().isoformat()) + '_all',
        rules=[],
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        loinc='./testdata/dictionaries/loinc',
        medrt='./testdata/dictionaries/medrt',
        unii='./testdata/dictionaries/unii',
        snomed_version='2024-09-01',
        snomed_edition='SNOMEDCT-US',
        progress='bar',
        max_errors_per_rule=(10, True)
    )

    validate(
        standard='sdtmig',
        version='3-3',
        cache='./resources/cache',
        dataset_path=['./testdata/sdtm/dm.xpt', './testdata/sdtm/ae.xpt'],
        report_template='./resources/templates/report-template.xlsx',
        output_format=['JSON', 'XLSX'],
        raw_report=False,
        output='./reports/' + generate_report_filename(datetime.now().isoformat()),
        rules=["CORE-000006", "CORE-000007", "CORE-000012", "CORE-000013", "CORE-000019", "CORE-000266", "CORE-000356"],
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        loinc='./testdata/dictionaries/loinc',
        medrt='./testdata/dictionaries/medrt',
        unii='./testdata/dictionaries/unii',
        snomed_version='2024-09-01',
        snomed_edition='SNOMEDCT-US',
        progress='bar'
    )

    validate(
        standard='mycustom',
        version='1-0',
        cache='./resources/cache',
        data='./testdata/sdtm',
        report_template='./resources/templates/report-template.xlsx',
        output_format=['JSON', 'XLSX'],
        raw_report=False,
        output='./reports/' + generate_report_filename(datetime.now().isoformat()) + '_custom',
        rules=[],
        custom_standard=True,
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        loinc='./testdata/dictionaries/loinc',
        medrt='./testdata/dictionaries/medrt',
        unii='./testdata/dictionaries/unii',
        snomed_version='2024-09-01',
        snomed_edition='SNOMEDCT-US',
        progress='bar'
    )

    test_validate('xpt')
