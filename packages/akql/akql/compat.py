import sys


PY2 = sys.version_info.major == 2

if PY2:
    binary_type = str
    text_type = unicode  # noqa: F821
else:
    binary_type = bytes
    text_type = str
