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

    current_path = os.getcwd()
    print(f"Current working directory: {current_path}")
    os.chdir(core_path)

    import json
    import pickle
    from cdisc_rules_engine.enums.default_file_paths import DefaultFilePaths

    # Load all rules
    rules_file = DefaultFilePaths.RULES_CACHE_FILE.value
    with open(os.path.join(cache_path, rules_file), "rb") as f:
        rules_data = pickle.load(f)
    rule_sets = set()
    report_data=[]
    for rule in rules_data.keys():
        standard, version = rule.split("/")[1:3]
        rule_set = f"{standard.upper()}, {version}"
        if rule_set not in rule_sets:
            print(rule_set)
            rule_sets.add(rule_set)
            report_data.append(rule_set)

    with open(output, "w") as f:
        json.dump(report_data, f)
