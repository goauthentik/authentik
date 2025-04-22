import math
from os import environ
from ssl import OPENSSL_VERSION

import pytest
from cryptography.hazmat.backends.openssl.backend import backend

from authentik import get_full_version

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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    current_id = int(environ.get("CI_RUN_ID", "0")) - 1
    total_ids = int(environ.get("CI_TOTAL_RUNS", "0"))

    if total_ids:
        num_tests = len(items)
        matrix_size = math.ceil(num_tests / total_ids)

        start = current_id * matrix_size
        end = (current_id + 1) * matrix_size

        deselected_items = items[:start] + items[end:]
        config.hook.pytest_deselected(items=deselected_items)
        items[:] = items[start:end]
        print(f" Executing {start} - {end} tests")
