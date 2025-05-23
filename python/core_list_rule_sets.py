def core_list_rule_sets(output: str, cache_path: str):
    """Output: """
    
    """
    Command to list the rule sets available in the cache.
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

    # Load all rules
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
