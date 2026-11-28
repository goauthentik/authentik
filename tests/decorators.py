import socket
from collections.abc import Callable
from functools import lru_cache, wraps
from os import environ, getenv
from typing import Any

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test.testcases import TransactionTestCase
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from structlog.stdlib import get_logger

IS_CI = "CI" in environ
RETRIES = int(environ.get("RETRIES", "3")) if IS_CI else 1
SHADOW_ROOT_RETRIES = 5

JSONType = dict[str, Any] | list[Any] | str | int | float | bool | None


def get_local_ip(override=True) -> str:
    """Get the local machine's IP"""
    if (local_ip := getenv("LOCAL_IP")) and override:
        return local_ip
    hostname = socket.gethostname()
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return "0.0.0.0"


@lru_cache
def get_loader():
    """Thin wrapper to lazily get a Migration Loader, only when it's needed
    and only once"""
    return MigrationLoader(connection)


def retry(max_retires=RETRIES, exceptions=None):
    """Retry test multiple times. Default to catching Selenium Timeout Exception"""

    if not exceptions:
        exceptions = [WebDriverException, TimeoutException, NoSuchElementException]

    logger = get_logger()

    def retry_actual(func: Callable):
        """Retry test multiple times"""

        @wraps(func)
        def wrapper(self: TransactionTestCase, *args, _count: int = 1, **kwargs):
            """Run test again if we're below max_retries, including tearDown and
            setUp. Otherwise raise the error"""
            try:
                return func(self, *args, **kwargs)

            except tuple(exceptions) as exc:
                if _count >= max_retires:
                    logger.debug("Exceeded retry count", exc=exc, test=self)

                    raise exc
                logger.debug("Retrying on error", exc=exc, test=self)
                self.tearDown()
                self._post_teardown()
                self._pre_setup()
                self.setUp()
                return wrapper(self, *args, _count=_count + 1, **kwargs)

        return wrapper

    return retry_actual
