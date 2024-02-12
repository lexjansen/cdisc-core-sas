def core_version():
  """Output: message_return_value"""

  import os
  import sys

  # Add top-level folder to path so that project folder can be found
  core_path = os.environ["CORE_PATH"]
  lib_path = os.path.abspath(os.path.join(__file__, core_path))
  if lib_path not in sys.path: sys.path.append(lib_path)

  from version import __version__

  return __version__
