import asyncio
import json
import logging
import os
import sys
import pickle
import tempfile
from datetime import datetime
from multiprocessing import freeze_support
from typing import Tuple

from pathlib import Path
from cdisc_rules_engine.config import config
from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
from cdisc_rules_engine.enums.progress_parameter_options import ProgressParameterOptions
from cdisc_rules_engine.enums.report_types import ReportTypes
from cdisc_rules_engine.enums.dataformat_types import DataFormatTypes
from cdisc_rules_engine.models.validation_args import Validation_args
from scripts.run_validation import run_validation
from cdisc_rules_engine.services.cache.cache_populator_service import CachePopulator
from cdisc_rules_engine.services.cache.cache_service_factory import CacheServiceFactory
from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService
from cdisc_rules_engine.models.external_dictionaries_container import (
    ExternalDictionariesContainer,
    DictionaryTypes,
)
from cdisc_rules_engine.utilities.utils import (
    generate_report_filename,
    get_rules_cache_key,
)
from scripts.list_dataset_metadata_handler import list_dataset_metadata_handler
from version import __version__


def valid_data_file(data_path: list) -> Tuple[list, set]:
    allowed_formats = [format.value for format in DataFormatTypes]
    found_formats = set()
    file_list = []
    for file in data_path:
        file_extension = os.path.splitext(file)[1][1:].upper()
        if file_extension in allowed_formats:
            found_formats.add(file_extension)
            file_list.append(file)
    if len(found_formats) > 1:
        return [], found_formats
    elif len(found_formats) == 1:
        return file_list, found_formats

def validate(
    standard: str = '',
    version: str = '',
    substandard: str = '',
    cache: str = DefaultFilePaths.CACHE.value,
    pool_size: int = 10,
    log_level: str = 'disabled',
    data: str = '',
    dataset_path: Tuple[str] = [],
    report_template: str = DefaultFilePaths.EXCEL_TEMPLATE_FILE.value,
    output_format: Tuple[str] = [ReportTypes.XLSX.value],
    raw_report: bool = False,
    output: str  = generate_report_filename(datetime.now().isoformat()),
    controlled_terminology_package: Tuple[str] = [],
    define_version: str = '',
    rules: Tuple[str] = [],
    local_rules: str = '',
    custom_standard: bool = False,
    define_xml_path: str = '',
    validate_xml: str ='',
    whodrug: str = '',
    meddra: str = '',
    loinc: str = '',
    medrt: str = '',
    unii: str =  '',
    snomed_version: str = '',
    snomed_edition: str = '',
    snomed_url: str = 'https://snowstorm.snomedtools.org/snowstorm/snomed-ct/',
    progress: str = 'disabled'
):
    """
    Validate data using CDISC Rules Engine

    Example:

    python core.py -s SDTM -v 3.4 -d /path/to/datasets
    """

    # Validate conditional options
    logger = logging.getLogger("validator")

    if raw_report is True:
        if not (len(output_format) == 1 and output_format[0] == ReportTypes.JSON.value):
            logger.error(
                "Flag --raw-report can be used only when --output-format is JSON"
            )
            return

    cache_path: str = os.path.join(os.path.dirname(__file__), cache)

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

    if data:
        if dataset_path:
            logger.error(
                "Argument --dataset-path cannot be used together with argument --data"
            )
            return
        dataset_paths, found_formats = valid_data_file(
            [str(Path(data).joinpath(fn)) for fn in os.listdir(data)]
        )
        if len(found_formats) > 1:
            logger.error(
                f"Argument --data contains more than one allowed file format ({', '.join(found_formats)})."  # noqa: E501
            )
            return
    elif dataset_path:
        dataset_paths, found_formats = valid_data_file([dp for dp in dataset_path])
        if len(found_formats) > 1:
            logger.error(
                f"Argument --dataset_path contains more than one allowed file format ({', '.join(found_formats)})."  # noqa: E501
            )
            return
    else:
        logger.error(
            "You must pass one of the following arguments: --dataset-path, --data"
        )
        # no need to define dataset_paths here, the program execution will stop
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
            set(controlled_terminology_package),  # avoiding duplicates
            output,
            set(output_format),  # avoiding duplicates
            raw_report,
            define_version,
            external_dictionaries,
            rules,
            local_rules,
            custom_standard,
            progress,
            define_xml_path,
            validate_xml_bool
        )
    )

def update_cache(
    apikey: str,
    cache_path: str = DefaultFilePaths.CACHE.value,
    custom_rules_directory: str = '',
    custom_rule: str = '',
    remove_custom_rules: str = '',
    update_custom_rule: str  = '',
    custom_standard: str = '',
    remove_custom_standard: str = ''
):
    cache = CacheServiceFactory(config).get_cache_service()
    library_service = CDISCLibraryService(apikey, cache)
    cache_populator = CachePopulator(
        cache,
        library_service,
        custom_rules_directory,
        custom_rule,
        remove_custom_rules,
        update_custom_rule,
        custom_standard,
        remove_custom_standard,
        cache_path,
    )
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

    print("Cache updated successfully")

def list_rules(
    standard: str,
    version: str,
    substandard: str,
    output: str,
    cache_path: str = DefaultFilePaths.CACHE.value,
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
    with open(output, "w") as f:
        json.dump(rules, f, indent=4)

def list_rule_sets(
    output: str,
    cache_path: str = DefaultFilePaths.CACHE.value
    ):
    """Lists all standards and versions for which rules are available."""
    rules_file = DefaultFilePaths.RULES_DICTIONARY.value
    with open(os.path.join(cache_path, rules_file), "rb") as f:
        rules_data = pickle.load(f)

    rule_sets = {}
    report_data=[]
    for key in rules_data.keys():
        if "/" in key:
            parts = key.split("/")
            standard = parts[0]
            version = parts[1]
            substandard = parts[2] if len(parts) > 2 else None
            if substandard:
                version_key = f"{version}/{substandard}"
            else:
                version_key = version
            if standard not in rule_sets:
                rule_sets[standard] = set()
            rule_sets[standard].add(version_key)

    for standard in sorted(rule_sets.keys()):
        versions = sorted(rule_sets[standard])
        for version in versions:
            print(f"{standard.upper()}, {version}")
            report_data.append(f"{standard.upper()}, {version}")

    with open(output, "w") as f:
        json.dump(report_data, f)

def list_dataset_metadata(
    dataset_path: Tuple[str],
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


# @click.command()
def version():
    print(__version__)

def list_ct(
    subsets: Tuple[str],
    output: str,
    cache_path: str = DefaultFilePaths.CACHE.value
    ):
    """
    Command to list the ct packages available in the cache.
    """
    if subsets:
        subsets = set([subset.lower() for subset in subsets])
    ctset=[]
    for file in os.listdir(cache_path):
        file_prefix = file[0:file.find('ct-')+2]
        if file_prefix.endswith("ct") and (not subsets or file_prefix in subsets):
            ct = os.path.splitext(file)[0]
            print(ct)
            ctset.append(ct)
    with open(output, "w") as f:
        json.dump(ctset, f)

def test_validate():
    """**Release Test** validate command for executable."""
    try:
        import sys
        import os
        from cdisc_rules_engine.models.validation_args import Validation_args
        from cdisc_rules_engine.models.external_dictionaries_container import (
            ExternalDictionariesContainer,
        )
        from cdisc_rules_engine.enums.report_types import ReportTypes
        from cdisc_rules_engine.enums.progress_parameter_options import (
            ProgressParameterOptions,
        )
        from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths

        base_path = os.path.join("testdata", "datasets")
        ts_path = os.path.join(base_path, "TS.json")
        ae_path = os.path.join(base_path, "ae.xpt")
        if not all(os.path.exists(path) for path in [ts_path, ae_path]):
            raise FileNotFoundError(
                "Test datasets not found in /testdata/datasets"
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = DefaultFilePaths.CACHE.value
            pool_size = 10
            log_level = "disabled"
            report_template = DefaultFilePaths.EXCEL_TEMPLATE_FILE.value
            standard = "sdtmig"
            version = "3.4"
            substandard = None
            controlled_terminology_package = set()
            json_output = os.path.join(temp_dir, "json_validation_output")
            xpt_output = os.path.join(temp_dir, "xpt_validation_output")
            output_format = {ReportTypes.XLSX.value}
            raw_report = False
            define_version = None
            external_dictionaries = ExternalDictionariesContainer({})
            rules = []
            local_rules = None
            custom_standard = False
            progress = ProgressParameterOptions.BAR.value
            define_xml_path = None
            validate_xml = False
            json_output = os.path.join(temp_dir, "json_validation_output")
            run_validation(
                Validation_args(
                    cache_path,
                    pool_size,
                    [ts_path],
                    log_level,
                    report_template,
                    standard,
                    version,
                    substandard,
                    controlled_terminology_package,
                    json_output,
                    output_format,
                    raw_report,
                    define_version,
                    external_dictionaries,
                    rules,
                    local_rules,
                    custom_standard,
                    progress,
                    define_xml_path,
                    validate_xml
                )
            )
            print("JSON validation completed successfully!")
            xpt_output = os.path.join(temp_dir, "xpt_validation_output")
            run_validation(
                Validation_args(
                    cache_path,
                    pool_size,
                    [ae_path],
                    log_level,
                    report_template,
                    standard,
                    version,
                    substandard,
                    controlled_terminology_package,
                    xpt_output,
                    output_format,
                    raw_report,
                    define_version,
                    external_dictionaries,
                    rules,
                    local_rules,
                    custom_standard,
                    progress,
                    define_xml_path,
                    validate_xml
                )
            )
            print("XPT validation completed successfully!")
        print("All validation tests completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"Validation test failed: {str(e)}")
        sys.exit(1)



if __name__ == "__main__":

    version()

    # update_cache(apikey=os.environ.get("CDISC_LIBRARY_API_KEY"), cache_path='./resources/cache')
    update_cache(apikey=os.environ.get("CDISC_LIBRARY_API_KEY"), cache_path='./resources/cache', remove_custom_rules='ALL')
    update_cache(apikey=os.environ.get("CDISC_LIBRARY_API_KEY"), cache_path='./resources/cache', custom_rules_directory='./testdata/rules')

    list_rule_sets(cache_path='./resources/cache', output="./json/core_rule_sets.json")
    list_rules(cache_path='./resources/cache', output="./json/core_rules_sdtmig_34.json", standard='sdtmig', version='3-4', substandard='')
    list_rules(cache_path='./resources/cache', output="./json/core_rules_sdtmig_32_custom123.json", standard='sdtmig', version='3-2', substandard='', custom_rules=True)
    list_rules(cache_path='./resources/cache', output="./json/core_rules_sdtmig_32.json", standard='sdtmig', version='3-2', substandard='')
    exit()

    list_ct(output="./json/core_ct.json", subsets=[])
    # list_dataset_metadata(output="./json/core_dataset_metadata.json", dataset_path=['./testdata/sdtm/dm.xpt', './testdata/sdtm/ae.xpt', './testdata/sdtm/ex.xpt', './testdata/sdtm/lb.xpt'])

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
        rules = [],
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        loinc='./testdata/dictionaries/loinc',
        medrt='./testdata/dictionaries/medrt',
        unii='./testdata/dictionaries/unii',
        snomed_version='2024-09-01',
        snomed_edition = 'SNOMEDCT-US',
        progress='bar'
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
        rules = ["CORE-000006", "CORE-000007", "CORE-000012", "CORE-000013", "CORE-000019", "CORE-000266", "CORE-000356"],
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        loinc='./testdata/dictionaries/loinc',
        medrt='./testdata/dictionaries/medrt',
        unii='./testdata/dictionaries/unii',
        snomed_version='2024-09-01',
        snomed_edition = 'SNOMEDCT-US',
        progress='bar'
    )

    validate(
        standard='sdtmig',
        version='3-2',
        cache='./resources/cache',
        data='./testdata/sdtm',
        report_template='./resources/templates/report-template.xlsx',
        output_format=['JSON', 'XLSX'],
        raw_report=False,
        output='./reports/' + generate_report_filename(datetime.now().isoformat()) + '_custom',
        rules = [],
        local_rules = './testdata/rules',
        custom_standard = False,
        define_xml_path='./testdata/sdtm/define.xml',
        whodrug='./testdata/dictionaries/whodrug',
        meddra='./testdata/dictionaries/meddra',
        loinc='./testdata/dictionaries/loinc',
        medrt='./testdata/dictionaries/medrt',
        unii='./testdata/dictionaries/unii',
        snomed_version='2024-09-01',
        snomed_edition = 'SNOMEDCT-US',
        progress='bar'
    )

    test_validate()