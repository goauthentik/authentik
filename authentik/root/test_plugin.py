import math
from os import environ
from ssl import OPENSSL_VERSION
from time import monotonic
from typing import TextIO

import pytest
from cryptography.hazmat.backends.openssl.backend import backend
from pytest import Config, Item, TerminalReporter

from authentik import authentik_full_version
from tests.decorators import get_local_ip

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
        f"authentik version: {authentik_full_version()}",
        f"OpenSSL version: {OPENSSL_VERSION}, FIPS: {backend._fips_enabled}",
        f"Local IP: {get_local_ip()} (Detected as {get_local_ip(override=False)})",
    ]


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
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


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config):
    # Replace the default terminal reporter
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter:
        config.pluginmanager.unregister(reporter)
        config.pluginmanager.register(
            RelativeTimeTerminalReporter(config),
            "terminalreporter",
        )


class RelativeTimeTerminalReporter(TerminalReporter):
    _start_time: None | float

    def __init__(self, config: Config, file: TextIO | None = None):
        super().__init__(config, file)
        self._start_time = None

    def pytest_runtest_logstart(self, nodeid, location):
        # Set start time on the first test
        if self._start_time is None:
            self._start_time = monotonic()
        super().pytest_runtest_logstart(nodeid, location)

    def _locationline(self, nodeid, fspath, lineno, domain):
        original = super()._locationline(nodeid, fspath, lineno, domain)
        if self._start_time is None:
            return original
        elapsed = monotonic() - self._start_time
        minutes, seconds = divmod(elapsed, 60)
        timestamp = f"{int(minutes):02d}:{seconds:06.3f}"
        return f"[+{timestamp}] {original}"
