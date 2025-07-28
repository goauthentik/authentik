#!/usr/bin/env python
"""Django manage.py"""

import os
import sys

from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

from authentik.root.setup import setup
from lifecycle.migrate import run_migrations
from lifecycle.wait_for_db import wait_for_db

setup()

if __name__ == "__main__":
    wait_for_db()
    if (
        len(sys.argv) > 1
        # Explicitly only run migrate for server and worker
        and sys.argv[1] in ["dev_server", "worker"]
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
