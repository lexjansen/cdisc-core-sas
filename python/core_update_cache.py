def core_update_cache(apikey, cache_path, local_rules, local_rules_id, remove_rules):
  """Output: """

  import os
  import sys

  # Add top-level folder to path so that project folder can be found
  core_path = os.environ["CORE_PATH"]
  lib_path = os.path.abspath(os.path.join(__file__, core_path))
  if lib_path not in sys.path: sys.path.append(lib_path)

  if not apikey:
    apikey = os.environ["CDISC_LIBRARY_API_KEY"]

  import asyncio
  from cdisc_rules_engine.config import config

  from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
  from cdisc_rules_engine.services.cache.cache_populator_service import CachePopulator
  from cdisc_rules_engine.services.cache.cache_service_factory import CacheServiceFactory
  from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService

  def update_cache(
      apikey: str,
      cache_path: str = DefaultFilePaths.CACHE.value,
      local_rules: str = '',
      local_rules_id: str = '',
      remove_rules: str = ''  
      ):
      cache = CacheServiceFactory(config).get_cache_service()
      library_service = CDISCLibraryService(apikey, cache)
      cache_populator = CachePopulator(
          cache, library_service, local_rules, local_rules_id, remove_rules, cache_path
      )
      cache = asyncio.run(cache_populator.load_cache_data())
      if remove_rules:
          cache_populator.save_removed_rules_locally(
              os.path.join(cache_path, DefaultFilePaths.LOCAL_RULES_CACHE_FILE.value),
              remove_rules,
          )
          print("Local rules removed from cache")
      elif local_rules and local_rules_id:
          cache_populator.save_local_rules_locally(
              os.path.join(cache_path, DefaultFilePaths.LOCAL_RULES_CACHE_FILE.value),
              local_rules_id,
          )
          print("Local rules saved to cache")
      else:
          cache_populator.save_rules_locally(
              os.path.join(cache_path, DefaultFilePaths.RULES_CACHE_FILE.value)
          )
          cache_populator.save_ct_packages_locally(f"{cache_path}")
          cache_populator.save_standards_metadata_locally(
              os.path.join(cache_path, DefaultFilePaths.STANDARD_DETAILS_CACHE_FILE.value)
          )
          cache_populator.save_standards_models_locally(
              os.path.join(cache_path, DefaultFilePaths.STANDARD_MODELS_CACHE_FILE.value)
          )
          cache_populator.save_variable_codelist_maps_locally(
              os.path.join(
                  cache_path, DefaultFilePaths.VARIABLE_CODELIST_CACHE_FILE.value
              )
          )
          cache_populator.save_variables_metadata_locally(
              os.path.join(
                  cache_path, DefaultFilePaths.VARIABLE_METADATA_CACHE_FILE.value
              )
          )
      print("Cache updated successfully")

  update_cache(
      apikey=apikey, 
      cache_path=cache_path, 
      local_rules=local_rules, 
      local_rules_id=local_rules_id, 
      remove_rules=remove_rules
      )
