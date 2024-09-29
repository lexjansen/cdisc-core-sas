def core_list_ct(subsets, output: str, cache_path: str):
    """Output: """
    
    """
    Command to list the ct packages available in the cache.
    """

    import os
    import sys

    # Add top-level folder to path so that project folder can be found
    core_path = os.environ["CORE_PATH"]
    lib_path = os.path.abspath(os.path.join(__file__, core_path))
    if lib_path not in sys.path: sys.path.append(lib_path)

    import json

    subsets = [item.strip(' ') for item in subsets if item !='']
    
    if subsets:
        subsets = set([subset.lower() for subset in subsets])
    ctset=[]
    for file in os.listdir(cache_path):
        file_prefix = file[0 : file.find("ct-") + 2]
        if file_prefix.endswith("ct") and (not subsets or file_prefix in subsets):
            ct = os.path.splitext(file)[0]
            print(ct)
            ctset.append(ct)
    with open(output, "w") as f:
        json.dump(ctset, f)
