def core_list_rules(output: str, standard: str, version: str, substandard: str, cache_path: str, custom_rules: bool, rule_id: str):
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

    os.chdir(core_path)
    print(f"Current working directory: {os.getcwd()}")

    import json
    import pickle
    from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths
    from cdisc_rules_engine.utilities.utils import (
        get_rules_cache_key
    )

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
        json.dump(rules, f)