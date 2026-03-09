def core_validate_data(cache, pool_size, data, filetype, dataset_path, log_level, report_template, standard, version, substandard, use_case,
                       output, output_format, raw_report, controlled_terminology_package, define_version, define_xml_path, validate_xml,
                       whodrug, meddra, loinc, medrt, unii, snomed_version, snomed_edition, snomed_url,
                       rules, exclude_rules, local_rules, custom_standard, jsonata_custom_functions, max_report_rows, max_errors_per_rule, encoding):
    """Output: message_return_value"""

    import os
    import sys

    # Add top-level folder to path so that project folder can be found
    core_path = os.environ["CORE_PATH"]
    lib_path = os.path.abspath(os.path.join(__file__, core_path))
    if lib_path not in sys.path: sys.path.append(lib_path)
      
    os.chdir(core_path)
    print(f"Current working directory: {os.getcwd()}")

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
    import re

    from cdisc_rules_engine.config import config
    from cdisc_rules_engine.enums.dataformat_types import DataFormatTypes
    from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
    from cdisc_rules_engine.enums.progress_parameter_options import ProgressParameterOptions
    from cdisc_rules_engine.enums.report_types import ReportTypes
    from cdisc_rules_engine.models.external_dictionaries_container import (
        ExternalDictionariesContainer,
        DictionaryTypes,
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
        standard: str,
        version: str,
        substandard: str = '',
        use_case: str = '',
        cache: str = core_path + "/" + DefaultFilePaths.CACHE.value,
        pool_size: int =10,
        log_level: str = 'disabled',
        data: str = '',
        filetype: str = '',
        dataset_path: tuple[str] =[],
        report_template: str = core_path + "/" + DefaultFilePaths.EXCEL_TEMPLATE_FILE.value,
        output_format: tuple[str] = [ReportTypes.XLSX.value],
        raw_report: bool = True,
        output: str = generate_report_filename(datetime.now().isoformat()),
        controlled_terminology_package: tuple[str] = [],
        define_version: str = '',
        rules: tuple[str] = [],
        exclude_rules: tuple[str] = [],
        local_rules: str = '',
        custom_standard: bool = False,
        define_xml_path: str = '',
        validate_xml: str = '',
        jsonata_custom_functions: tuple[str] = [],
        whodrug: str ='',
        meddra: str = '',
        loinc: str = '',
        medrt: str = '',
        unii: str =  '',
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

        validation_message = ""

        dataset_path = [item.strip(' ') for item in dataset_path if item !='']
        output_format = [item.strip(' ') for item in output_format if item !='']
        controlled_terminology_package = [item.strip(' ') for item in controlled_terminology_package if item !='']
        rules = [item.strip(' ') for item in rules if item !='']
        exclude_rules = [item.strip(' ') for item in exclude_rules if item !='']
        jsonata_custom_functions = [item.strip(' ') for item in jsonata_custom_functions if item !='']

        # Strip parentheses and split
        parts = max_errors_per_rule.strip("()").split()
        max_errors_per_rule = (int(parts[0].strip()), bool(int(parts[1].strip())))



        if not log_level:
            log_level = 'disabled'

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
                validation_message = "Flag --raw-report can be used only when --output-format is JSON"
                return validation_message

        if exclude_rules and rules:
            logger.error("Cannot use both --rules and --exclude-rules flags together.")
            validation_message = "Cannot use both --rules and --exclude-rules flags together."
            return validation_message

        cache_path: str = os.path.join(os.path.dirname(__file__), cache)

        if standard == "tig":
            if not substandard or not use_case:
                logger.error(
                    "Standard 'tig' requires both --substandard and --use-case to be specified."
                )
                validation_message = "Standard 'tig' requires both --substandard and --use-case to be specified."
                return validation_message

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
                validation_message = "Argument --dataset_path cannot be used together with argument --data"
                return validation_message
            dataset_paths, found_formats = _validate_data_directory(data, logger, filetype)
            if not dataset_paths:
                validation_message = "dataset_path not found"
                return validation_message
        elif dataset_path:
            dataset_paths, found_formats = _validate_dataset_paths(dataset_path, logger)
            if not dataset_paths:
                validation_message = "dataset_path not found"
                return validation_message
        else:
            _validate_no_arguments(logger)
            validation_message = "_validate_no_arguments"
            return validation_message


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
                set(controlled_terminology_package),  # avoiding duplicates
                output,
                set(output_format),  # avoiding duplicates
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

        return validation_message

    return_message = validate(
         cache=cache,
         pool_size=int(pool_size),
         data=data,
         filetype=filetype,
         dataset_path=re.split(';|,', dataset_path),
         log_level=log_level,
         report_template=report_template,
         standard=standard,
         version=version,
         substandard=substandard,
         use_case=use_case,
         output=output,
         output_format=re.split(';|,', output_format),
         raw_report=(raw_report == 1),
         controlled_terminology_package=re.split(';|,', controlled_terminology_package),
         define_version=define_version,
         whodrug=whodrug,
         meddra=meddra,
         loinc=loinc,
         medrt=medrt,
         unii=unii,
         snomed_version=snomed_version,
         snomed_edition=snomed_edition,
         snomed_url=snomed_url,
         rules=re.split(';|,', rules),
         exclude_rules=re.split(';|,', exclude_rules),
         local_rules=local_rules,
         custom_standard=custom_standard,
         define_xml_path=define_xml_path,
         validate_xml=validate_xml,
         jsonata_custom_functions=re.split(';|,', jsonata_custom_functions),
         max_report_rows=max_report_rows,
         max_errors_per_rule=max_errors_per_rule,
         encoding=encoding,
     )

    return return_message