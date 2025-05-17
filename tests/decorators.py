"""authentik e2e testing utilities"""

from collections.abc import Callable
from functools import wraps

from django.test.testcases import TransactionTestCase
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from structlog.stdlib import get_logger

from tests import RETRIES


def retry(max_retires=RETRIES, exceptions=None):
    """Retry test multiple times. Default to catching Selenium Timeout Exception"""

    if not exceptions:
        exceptions = [WebDriverException, TimeoutException, NoSuchElementException]

    logger = get_logger()

    def retry_actual(func: Callable):
        """Retry test multiple times"""
        count = 1

        @wraps(func)
        def wrapper(self: TransactionTestCase, *args, **kwargs):
            """Run test again if we're below max_retries, including tearDown and
            setUp. Otherwise raise the error"""
            nonlocal count
            try:
                return func(self, *args, **kwargs)

            except tuple(exceptions) as exc:
                count += 1
                if count > max_retires:
                    logger.debug("Exceeded retry count", exc=exc, test=self)

                    raise exc
                logger.debug("Retrying on error", exc=exc, test=self)
                self.tearDown()
                self._post_teardown()
                self._pre_setup()
                self.setUp()
                return wrapper(self, *args, **kwargs)

        return wrapper

    return retry_actual
