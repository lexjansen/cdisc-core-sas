def core_list_dataset_metadata(dataset_path, output: str):
    """Output: """

    """
    Command that lists metadata of given datasets.

    Input:
        core.py list-ds-metadata -dp=path_1 -dp=path_2 -dp=path_3 ...
    Output:
        [
           {
              "domain":"AE",
              "filename":"ae.xpt",
              "full_path":"/Users/Aleksei_Furmenkov/PycharmProjects/cdisc-rules-engine/resources/data/ae.xpt",
              "size":"38000",
              "label":"Adverse Events",
              "modification_date":"2020-08-21T09:14:26"
           },
           {
              "domain":"EX",
              "filename":"ex.xpt",
              "full_path":"/Users/Aleksei_Furmenkov/PycharmProjects/cdisc-rules-engine/resources/data/ex.xpt",
              "size":"78050",
              "label":"Exposure",
              "modification_date":"2021-09-17T09:23:22"
           },
           ...
        ]
    """

    import os
    import sys

    # Add top-level folder to path so that project folder can be found
    core_path = os.environ["CORE_PATH"]
    lib_path = os.path.abspath(os.path.join(__file__, core_path))
    if lib_path not in sys.path: sys.path.append(lib_path)

    import json
    from scripts.list_dataset_metadata_handler import list_dataset_metadata_handler
    import re

    dataset_path = re.split(';|,', dataset_path)
    dataset_path = [item.strip(' ') for item in dataset_path if item !='']
    
    with open(output, "w") as f:
        json.dump(list_dataset_metadata_handler(dataset_path), f)
