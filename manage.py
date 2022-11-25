#!/usr/bin/env python
"""Django manage.py"""
import os
import sys
import warnings

from defusedxml import defuse_stdlib

warnings.filterwarnings("ignore", "SelectableGroups dict interface")
warnings.filterwarnings(
    "ignore",
    "defusedxml.lxml is no longer supported and will be removed in a future release.",
)
warnings.filterwarnings(
    "ignore",
    "defusedxml.cElementTree is deprecated, import from defusedxml.ElementTree instead.",
)

defuse_stdlib()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
