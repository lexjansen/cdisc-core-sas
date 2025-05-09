def core_validate_data(cache, pool_size, data, dataset_path, log_level, report_template, standard, version, substandard,
                       output, output_format, raw_report, controlled_terminology_package, define_version, define_xml_path, validate_xml,
                       whodrug, meddra, loinc, medrt, unii, snomed_version, snomed_edition, snomed_url,
                       rules, local_rules, custom_standard):
      """Output: message_return_value"""

      import os
      import sys

      # Add top-level folder to path so that project folder can be found
      core_path = os.environ["CORE_PATH"]
      lib_path = os.path.abspath(os.path.join(__file__, core_path))
      if lib_path not in sys.path: sys.path.append(lib_path)
        
      current_path = os.getcwd()
      print(f"Current working directory: {current_path}")
      os.chdir(core_path)

      import asyncio
      import json
      import logging
      import os
      import pickle
      from datetime import datetime
      from multiprocessing import freeze_support
      from typing import Tuple
      import re

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
      from cdisc_rules_engine.utilities.utils import generate_report_filename
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
          standard: str,
          version: str,
          substandard: str = '',
          cache: str = core_path + "/" + DefaultFilePaths.CACHE.value,
          pool_size: int =10,
          log_level: str = 'disabled',
          data: str = '',
          dataset_path: Tuple[str] =[],
          report_template: str = core_path + "/" + DefaultFilePaths.EXCEL_TEMPLATE_FILE.value,
          output_format: Tuple[str] = [ReportTypes.XLSX.value],
          raw_report: bool = True,
          output: str = generate_report_filename(datetime.now().isoformat()),
          controlled_terminology_package: Tuple[str] = [],
          define_version: str = '',
          rules: Tuple[str] = [],
          local_rules: str = '',
          custom_standard: bool = False,
          define_xml_path: str = '',
          validate_xml: str = '',
          whodrug: str ='',
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

          validation_message = ""

          dataset_path = [item.strip(' ') for item in dataset_path if item !='']
          output_format = [item.strip(' ') for item in output_format if item !='']
          controlled_terminology_package = [item.strip(' ') for item in controlled_terminology_package if item !='']
          rules = [item.strip(' ') for item in rules if item !='']


          if not log_level:
              log_level = 'disabled'

          # Validate conditional options
          logger = logging.getLogger("validator")

          if raw_report is True:
              if not (len(output_format) == 1 and output_format[0] == ReportTypes.JSON.value):
                  logger.error(
                      "Flag --raw-report can be used only when --output-format is JSON"
                  )
                  validation_message = "Flag --raw-report can be used only when --output-format is JSON"
                  return validation_message

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
                  validation_message = "Argument --dataset-path cannot be used together with argument --data"
                  return validation_message
              dataset_paths, found_formats = valid_data_file(
                  [str(Path(data).joinpath(fn)) for fn in os.listdir(data)]
              )
              if len(found_formats) > 1:
                  logger.error(
                      f"Argument --data contains more than one allowed file format ({', '.join(found_formats)})."
                  )
                  validation_message = "Argument --data contains more than one allowed file format: " + ", ".join(found_formats)
                  return validation_message
          elif dataset_path:
              dataset_paths, found_formats = valid_data_file([dp for dp in dataset_path])
              if len(found_formats) > 1:
                  logger.error(
                      f"Argument --dataset-path contains more than one allowed file format ({', '.join(found_formats)})."
                  )
                  validation_message = "Argument --dataset-path contains more than one allowed file format: " + ", ".join(found_formats)
                  return validation_message
          else:
              logger.error(
                  "You must pass one of the following arguments: --dataset-path, --data"
              )
              validation_message = "You must pass one of the following arguments: --dataset-path, --data"
              # no need to define dataset_paths here, the program execution will stop
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

          return validation_message

      return_message = validate(
           cache=cache,
           pool_size=int(pool_size),
           data=data,
           dataset_path=re.split(';|,', dataset_path),
           log_level=log_level,
           report_template=report_template,
           standard=standard,
           version=version,
           substandard=substandard,
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
           local_rules=local_rules,
           custom_standard=custom_standard,
           define_xml_path=define_xml_path,
           validate_xml=validate_xml
       )

      return return_message