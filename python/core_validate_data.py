def core_validate_data(cache, pool_size, data, dataset_path, log_level, report_template, standard, version, 
                           output, output_format, raw_report, controlled_terminology_package, define_version, data_format, define_xml_path, whodrug, meddra, rules):
      """Output: message_return_value"""

      import os
      import sys

      # Add top-level folder to path so that project folder can be found
      core_path = os.environ["CORE_PATH"]
      lib_path = os.path.abspath(os.path.join(__file__, core_path))
      if lib_path not in sys.path: sys.path.append(lib_path)

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
      from cdisc_rules_engine.constants.define_xml_constants import DEFINE_XML_FILE_NAME
      from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
      from cdisc_rules_engine.enums.progress_parameter_options import ProgressParameterOptions
      from cdisc_rules_engine.enums.report_types import ReportTypes
      from cdisc_rules_engine.models.validation_args import Validation_args
      from scripts.run_validation import run_validation
      from cdisc_rules_engine.services.cache.cache_populator_service import CachePopulator
      from cdisc_rules_engine.services.cache.cache_service_factory import CacheServiceFactory
      from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService
      from cdisc_rules_engine.utilities.utils import (
          generate_report_filename,
          get_rules_cache_key,
      )
      from scripts.list_dataset_metadata_handler import list_dataset_metadata_handler
      from version import __version__

      def valid_data_file(file_name: str, data_format: str):
          fn = os.path.basename(file_name)
          return fn.lower() != DEFINE_XML_FILE_NAME and fn.lower().endswith(
              f".{data_format.lower()}"
          )
    
      def validate(
          standard: str,
          version: str,
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
          data_format: str = "XPT",
          rules: Tuple[str] = [],
          define_xml_path: str = '',
          whodrug: str ='',
          meddra: str = '',
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

          if data:
              if dataset_path:
                  logger.error(
                      "Argument --dataset-path cannot be used together with argument --data"
                  )
                  validation_message = "Argument --dataset-path cannot be used together with argument --data"
                  return validation_message
              dataset_paths: Iterable[str] = [
                  str(Path(data).joinpath(fn))
                  for fn in os.listdir(data)
                  if valid_data_file(fn, data_format)
              ]
          elif dataset_path:
              if data:
                  logger.error(
                      "Argument --dataset-path cannot be used together with argument --data"
                  )
                  validation_message = "Argument --dataset-path cannot be used together with argument --data"
                  return validation_message
              dataset_paths: Iterable[str] = [
                  dp for dp in dataset_path if valid_data_file(dp, data_format)
              ]
          else:
              logger.error(
                  "You must pass one of the following arguments: --dataset-path, --data"
              )
              validation_message = "You must pass one of the following arguments: --dataset-path, --data"
              # no need to define dataset_paths here, the program execution will stop
              return validation_message

          run_validation(
              Validation_args(
                  cache_path,
                  pool_size,
                  dataset_paths,
                  log_level,
                  report_template,
                  standard,
                  version,
                  set(controlled_terminology_package),  # avoiding duplicates
                  output,
                  set(output_format),  # avoiding duplicates
                  raw_report,
                  define_version,
                  data_format.lower(),
                  whodrug,
                  meddra,
                  rules,
                  progress,
                  define_xml_path,
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
           output=output,
           output_format=re.split(';|,', output_format),
           raw_report=(raw_report == 1),
           controlled_terminology_package=re.split(';|,', controlled_terminology_package),
           define_version=define_version,
           data_format=data_format,
           whodrug=whodrug,
           meddra=meddra,
           rules=re.split(';|,', rules)
       )
       
      return return_message