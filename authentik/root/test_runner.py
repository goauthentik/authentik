"""Integrate ./manage.py test with pytest"""

import os
from argparse import ArgumentParser
from unittest import TestCase

import pytest
from django.conf import settings
from django.test.runner import DiscoverRunner

from authentik.lib.config import CONFIG
from authentik.lib.sentry import sentry_init
from authentik.root.signals import post_startup, pre_startup, startup
from tests.e2e.utils import get_docker_tag

# globally set maxDiff to none to show full assert error
TestCase.maxDiff = None


class PytestTestRunner(DiscoverRunner):  # pragma: no cover
    """Runs pytest to discover and run tests."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.args = []
        if self.failfast:
            self.args.append("--exitfirst")
        if self.keepdb:
            self.args.append("--reuse-db")

        if kwargs.get("randomly_seed", None):
            self.args.append(f"--randomly-seed={kwargs['randomly_seed']}")

        settings.TEST = True
        settings.CELERY["task_always_eager"] = True
        CONFIG.set("events.context_processors.geoip", "tests/GeoLite2-City-Test.mmdb")
        CONFIG.set("events.context_processors.asn", "tests/GeoLite2-ASN-Test.mmdb")
        CONFIG.set("blueprints_dir", "./blueprints")
        CONFIG.set(
            "outposts.container_image_base",
            f"ghcr.io/goauthentik/dev-%(type)s:{get_docker_tag()}",
        )
        CONFIG.set("tenants.enabled", False)
        CONFIG.set("outposts.disable_embedded_outpost", False)
        CONFIG.set("error_reporting.sample_rate", 0)
        CONFIG.set("error_reporting.environment", "testing")
        CONFIG.set("error_reporting.send_pii", True)
        sentry_init()

        pre_startup.send(sender=self, mode="test")
        startup.send(sender=self, mode="test")
        post_startup.send(sender=self, mode="test")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser):
        """Add more pytest-specific arguments"""
        DiscoverRunner.add_arguments(parser)
        parser.add_argument(
            "--randomly-seed",
            type=int,
            help="Set the seed that pytest-randomly uses (int), or pass the special value 'last'"
            "to reuse the seed from the previous run."
            "Default behaviour: use random.Random().getrandbits(32), so the seed is"
            "different on each run.",
        )

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Run pytest and return the exitcode.

        It translates some of Django's test command option to pytest's.
        It is supported to only run specific classes and methods using
        a dotted module name i.e. foo.bar[.Class[.method]]

        The extra_tests argument has been deprecated since Django 5.x
        It is kept for compatibility with PyCharm's Django test runner.
        """

        for label in test_labels:
            valid_label_found = False
            label_as_path = os.path.abspath(label)
            # File path has been specified
            if os.path.exists(label_as_path):
                self.args.append(label_as_path)
                valid_label_found = True
            elif "::" in label:
                self.args.append(label)
                valid_label_found = True
            # Convert dotted module path to file_path::class::method
            else:
                path_pieces = label.split(".")
                # Check whether only class or class and method are specified
                for i in range(-1, -3, -1):
                    path = os.path.join(*path_pieces[:i]) + ".py"
                    label_as_path = os.path.abspath(path)
                    if os.path.exists(label_as_path):
                        path_method = label_as_path + "::" + "::".join(path_pieces[i:])
                        self.args.append(path_method)
                        valid_label_found = True
                        break

            if not valid_label_found:
                raise RuntimeError(
                    f"One of the test labels: {label!r}, "
                    f"is not supported. Use a dotted module name or "
                    f"path instead."
                )

        return pytest.main(self.args)
