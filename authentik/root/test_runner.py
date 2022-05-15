"""Integrate ./manage.py test with pytest"""
from argparse import ArgumentParser

from django.conf import settings

from authentik.lib.config import CONFIG
from authentik.lib.sentry import sentry_init
from tests.e2e.utils import get_docker_tag


class PytestTestRunner:  # pragma: no cover
    """Runs pytest to discover and run tests."""

    def __init__(self, verbosity=1, failfast=False, keepdb=False, **kwargs):
        self.verbosity = verbosity
        self.failfast = failfast
        self.keepdb = keepdb

        self.args = ["-vv", "-s"]
        if self.failfast:
            self.args.append("--exitfirst")
        if self.keepdb:
            self.args.append("--reuse-db")

        if kwargs.get("randomly_seed", None):
            self.args.append(f"--randomly-seed={kwargs['randomly_seed']}")

        settings.TEST = True
        settings.CELERY_TASK_ALWAYS_EAGER = True
        CONFIG.y_set("avatars", "none")
        CONFIG.y_set("geoip", "tests/GeoLite2-City-Test.mmdb")
        CONFIG.y_set(
            "outposts.container_image_base",
            f"ghcr.io/goauthentik/dev-%(type)s:{get_docker_tag()}",
        )
        sentry_init(
            sample_rate=1.0,
            environment="testing",
            send_default_pii=True,
        )

    @classmethod
    def add_arguments(cls, parser: ArgumentParser):
        """Add more pytest-specific arguments"""
        parser.add_argument("--randomly-seed", type=int)

    def run_tests(self, test_labels):
        """Run pytest and return the exitcode.

        It translates some of Django's test command option to pytest's.
        """

        import pytest

        if any("tests/e2e" in label for label in test_labels):
            self.args.append("-pno:randomly")
        self.args.extend(test_labels)
        return pytest.main(self.args)
