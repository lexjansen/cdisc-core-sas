def core_list_rules(output: str, standard: str, version: str, cache_path: str, local_rules: bool, local_rules_id: str):
    """Output: """

    """
    Command to list the rule available in the cache.
    """

    import os
    import sys

    # Add top-level folder to path so that project folder can be found
    core_path = os.environ["CORE_PATH"]
    lib_path = os.path.abspath(os.path.join(__file__, core_path))
    if lib_path not in sys.path: sys.path.append(lib_path)

    current_path = os.getcwd()
    print(f"Current working directory: {current_path}")
    os.chdir(core_path)

    import json
    import pickle
    from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
    from cdisc_rules_engine.utilities.utils import (
        get_rules_cache_key,
        get_local_cache_key
    )

    # Load all rules
    if local_rules:
        rules_file = DefaultFilePaths.LOCAL_RULES_CACHE_FILE.value
    else:
        rules_file = DefaultFilePaths.RULES_CACHE_FILE.value
    with open(os.path.join(cache_path, rules_file), "rb") as f:
        rules_data = pickle.load(f)
    if not local_rules and (standard and version):
        key_prefix = get_rules_cache_key(standard, version.replace(".", "-"))
        rules = [rule for key, rule in rules_data.items() if key.startswith(key_prefix)]
    elif local_rules and local_rules_id:
        key_prefix = get_local_cache_key(local_rules_id)
        rules = [rule for key, rule in rules_data.items() if key.startswith(key_prefix)]
    else:
        # Print all rules
        rules = list(rules_data.values())
    with open(output, "w") as f:
        json.dump(rules, f, indent=4)
