"""Integrate ./manage.py test with pytest"""
from django.conf import settings

from authentik.lib.config import CONFIG


class PytestTestRunner:
    """Runs pytest to discover and run tests."""

    def __init__(self, verbosity=1, failfast=False, keepdb=False, **_):
        self.verbosity = verbosity
        self.failfast = failfast
        self.keepdb = keepdb
        settings.TEST = True
        settings.CELERY_TASK_ALWAYS_EAGER = True
        CONFIG.raw.get("authentik")["avatars"] = "none"

    def run_tests(self, test_labels):
        """Run pytest and return the exitcode.

        It translates some of Django's test command option to pytest's.
        """
        import pytest

        argv = []
        if self.verbosity == 0:
            argv.append("--quiet")
        if self.verbosity == 2:
            argv.append("--verbose")
        if self.verbosity == 3:
            argv.append("-vv")
        if self.failfast:
            argv.append("--exitfirst")
        if self.keepdb:
            argv.append("--reuse-db")

        argv.extend(test_labels)
        return pytest.main(argv)
