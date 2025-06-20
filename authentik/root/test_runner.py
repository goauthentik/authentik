"""Integrate ./manage.py test with pytest"""

import os
from argparse import ArgumentParser
from unittest import TestCase
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test.runner import DiscoverRunner
from structlog.stdlib import get_logger

from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR
from authentik.lib.config import CONFIG
from authentik.lib.sentry import sentry_init
from authentik.root.signals import post_startup, pre_startup, startup

# globally set maxDiff to none to show full assert error
TestCase.maxDiff = None


def get_docker_tag() -> str:
    """Get docker-tag based off of CI variables"""
    env_pr_branch = "GITHUB_HEAD_REF"
    default_branch = "GITHUB_REF"
    branch_name = os.environ.get(default_branch, "main")
    if os.environ.get(env_pr_branch, "") != "":
        branch_name = os.environ[env_pr_branch]
    branch_name = branch_name.replace("refs/heads/", "").replace("/", "-")
    return f"gh-{branch_name}"


def patched__get_ct_cached(app_label, codename):
    """Caches `ContentType` instances like its `QuerySet` does."""
    return ContentType.objects.get(app_label=app_label, permission__codename=codename)


class PytestTestRunner(DiscoverRunner):  # pragma: no cover
    """Runs pytest to discover and run tests."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger().bind(runner="pytest")

        self.args = []
        if self.failfast:
            self.args.append("--exitfirst")
        if self.keepdb:
            self.args.append("--reuse-db")

        if kwargs.get("randomly_seed", None):
            self.args.append(f"--randomly-seed={kwargs['randomly_seed']}")
        if kwargs.get("no_capture", False):
            self.args.append("--capture=no")

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

        ASN_CONTEXT_PROCESSOR.load()
        GEOIP_CONTEXT_PROCESSOR.load()

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
        parser.add_argument(
            "--no-capture",
            action="store_true",
            help="Disable any capturing of stdout/stderr during tests.",
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

        self.logger.info("Running tests", test_files=self.args)
        with patch("guardian.shortcuts._get_ct_cached", patched__get_ct_cached):
            try:
                return pytest.main(self.args)
            except Exception as e:
                self.logger.error("Error running tests", error=str(e), test_files=self.args)
                return 1
