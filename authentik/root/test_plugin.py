from os import environ

import pytest

from authentik import get_full_version
from ssl import OPENSSL_VERSION
from cryptography.hazmat.backends.openssl.backend import backend

IS_CI = "CI" in environ


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionstart(*_, **__):
    """Clear the console ahead of the pytest output starting"""
    if not IS_CI:
        print("\x1b[2J\x1b[H")
    yield


@pytest.hookimpl(trylast=True)
def pytest_report_header(*_, **__):
    """Add authentik version to pytest output"""
    return [
        f"authentik version: {get_full_version()}",
        f"OpenSSL version: {OPENSSL_VERSION}, FIPS: {backend._fips_enabled}",
    ]
