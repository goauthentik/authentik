#!/usr/bin/env python
"""Django manage.py"""
import os
import sys
import warnings

from authentik.common.config import CONFIG
from cryptography.hazmat.backends.openssl.backend import backend
from defusedxml import defuse_stdlib
from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from lifecycle.migrate import run_migrations
from lifecycle.wait_for_db import wait_for_db

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

if CONFIG.get_bool("compliance.fips.enabled", False):
    backend._enable_fips()


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
    wait_for_db()
    if (
        len(sys.argv) > 1
        # Explicitly only run migrate for server and worker
        # `bootstrap_tasks` is a special case as that command might be triggered by the `ak`
        # script to pre-run certain tasks for an automated install
        and sys.argv[1] in ["dev_server", "worker", "bootstrap_tasks"]
        # and don't run if this is the child process of a dev_server
        and os.environ.get(DJANGO_AUTORELOAD_ENV, None) is None
    ):
        run_migrations()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
