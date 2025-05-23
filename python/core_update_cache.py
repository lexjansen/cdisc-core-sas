def core_update_cache(apikey, cache_path, custom_rules_directory, custom_rule, remove_custom_rules, update_custom_rule, custom_standard, remove_custom_standard):
    """Output: """

    import os
    import sys

    # Add top-level folder to path so that project folder can be found
    core_path = os.environ["CORE_PATH"]
    lib_path = os.path.abspath(os.path.join(__file__, core_path))
    if lib_path not in sys.path: sys.path.append(lib_path)

    os.chdir(core_path)
    print(f"Current working directory: {os.getcwd()}")

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
        custom_rules_directory: str = '', 
        custom_rule: str = '', 
        remove_custom_rules: str = '', 
        update_custom_rule: str = '', 
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

    update_cache(
        apikey=apikey,
        cache_path=cache_path,
        custom_rules_directory = custom_rules_directory,
        custom_rule = custom_rule,
        remove_custom_rules = remove_custom_rules,
        update_custom_rule = update_custom_rule,
        custom_standard = custom_standard,
        remove_custom_standard = remove_custom_standard
        )
