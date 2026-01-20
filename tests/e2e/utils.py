"""authentik e2e testing utilities"""

import socket
from collections.abc import Callable
from functools import lru_cache, wraps
from json import JSONDecodeError, dumps, loads
from os import environ, getenv
from sys import stderr
from time import sleep
from typing import Any
from urllib.parse import urlencode

from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test.testcases import TransactionTestCase
from django.urls import reverse
from dramatiq import get_broker
from selenium import webdriver
from selenium.common.exceptions import (
    DetachedShadowRootException,
    NoSuchElementException,
    NoSuchShadowRootException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from structlog.stdlib import get_logger

from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.tasks.test import use_test_broker
from tests.docker import DockerTestCase

IS_CI = "CI" in environ
RETRIES = int(environ.get("RETRIES", "3")) if IS_CI else 1
SHADOW_ROOT_RETRIES = 5

JSONType = dict[str, Any] | list[Any] | str | int | float | bool | None


def get_local_ip(override=True) -> str:
    """Get the local machine's IP"""
    if (local_ip := getenv("LOCAL_IP")) and override:
        return local_ip
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)
    return ip_addr


class SeleniumTestCase(DockerTestCase, StaticLiveServerTestCase):
    """StaticLiveServerTestCase which automatically creates a Webdriver instance"""

    host = get_local_ip()
    wait_timeout: int
    user: User

    def setUp(self):
        if IS_CI:
            print("::group::authentik Logs", file=stderr)
        apps.get_app_config("authentik_tenants").ready()
        self.wait_timeout = 60
        self.logger = get_logger()
        self.driver = self._get_driver()
        self.driver.implicitly_wait(30)
        self.wait = WebDriverWait(self.driver, self.wait_timeout)
        self.user = create_test_admin_user()
        super().setUp()

    def _get_driver(self) -> WebDriver:
        count = 0
        opts = webdriver.ChromeOptions()
        opts.add_argument("--disable-search-engine-choice-screen")
        # This breaks selenium when running remotely...?
        # opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        opts.add_experimental_option(
            "prefs",
            {
                "profile.password_manager_leak_detection": False,
            },
        )
        while count < RETRIES:
            try:
                driver = webdriver.Remote(
                    command_executor="http://localhost:4444/wd/hub",
                    options=opts,
                )
                driver.maximize_window()
                return driver
            except WebDriverException as exc:
                self.logger.warning("Failed to setup webdriver", exc=exc)
                count += 1
        raise ValueError(f"Webdriver failed after {RETRIES}.")

    @classmethod
    def _pre_setup(cls):
        use_test_broker()
        return super()._pre_setup()

    def _post_teardown(self):
        broker = get_broker()
        broker.flush_all()
        broker.close()
        return super()._post_teardown()

    def tearDown(self):
        if IS_CI:
            print("::endgroup::", file=stderr)
        super().tearDown()
        if IS_CI:
            print("::group::Browser logs")
        # Very verbose way to get browser logs
        # https://github.com/SeleniumHQ/selenium/pull/15641
        # for some reason this removes the `get_log` API from Remote Webdriver
        # and only keeps it on the local Chrome web driver, even when using
        # a remote chrome driver...? (nvm the fact this was released as a minor version)
        for line in self.driver.execute(Command.GET_LOG, {"type": "browser"})["value"]:
            print(line["message"])
        if IS_CI:
            print("::endgroup::")
        self.driver.quit()

    def wait_for_url(self, desired_url: str):
        """Wait until URL is `desired_url`."""

        self.wait.until(
            lambda driver: driver.current_url == desired_url,
            f"URL {self.driver.current_url} doesn't match expected URL {desired_url}. "
            f"HTML: {self.driver.page_source[:1000]}",
        )

    def url(self, view: str, query: dict | None = None, **kwargs) -> str:
        """reverse `view` with `**kwargs` into full URL using live_server_url"""
        url = self.live_server_url + reverse(view, kwargs=kwargs)
        if query:
            return url + "?" + urlencode(query)
        return url

    def if_user_url(self, path: str | None = None) -> str:
        """same as self.url() but show URL in shell"""
        url = self.url("authentik_core:if-user")
        if path:
            return f"{url}#{path}"
        return url

    def parse_json_content(
        self, context: WebElement | None = None, timeout: float | None = 10
    ) -> JSONType:
        """
        Parse JSON from a Selenium element's text content.

        If `context` is not provided, defaults to the <body> element.
        Raises a clear test failure if the element isn't found, the text doesn't appear
        within `timeout` seconds, or the text is not valid JSON.
        """
        use_body = context is None
        wait_timeout = timeout or self.wait_timeout

        def get_context() -> WebElement:
            """Get or refresh the context element."""
            if use_body:
                return self.driver.find_element(By.TAG_NAME, "body")
            return context

        def get_text_safely() -> str:
            """Get element text, re-finding element if stale."""
            for _ in range(5):
                try:
                    return get_context().text.strip()
                except StaleElementReferenceException:
                    sleep(0.5)
            return get_context().text.strip()

        def get_inner_html_safely() -> str:
            """Get innerHTML, re-finding element if stale."""
            for _ in range(5):
                try:
                    return get_context().get_attribute("innerHTML") or ""
                except StaleElementReferenceException:
                    sleep(0.5)
            return get_context().get_attribute("innerHTML") or ""

        try:
            get_context()
        except NoSuchElementException:
            self.fail(
                f"No element found (defaulted to <body>). Current URL: {self.driver.current_url}"
            )

        wait = WebDriverWait(self.driver, wait_timeout)

        try:
            wait.until(lambda d: len(get_text_safely()) != 0)
        except TimeoutException:
            snippet = get_text_safely()[:500].replace("\n", " ")
            self.fail(
                f"Timed out waiting for element text to appear at {self.driver.current_url}. "
                f"Current content: {snippet or '<empty>'}"
            )

        body_text = get_text_safely()
        inner_html = get_inner_html_safely()

        if "redirecting" in inner_html.lower():
            try:
                wait.until(lambda d: "redirecting" not in get_inner_html_safely().lower())
            except TimeoutException:
                snippet = get_text_safely()[:500].replace("\n", " ")
                inner_html = get_inner_html_safely()

                self.fail(
                    f"Timed out waiting for redirect to finish at {self.driver.current_url}. "
                    f"Current content: {snippet or '<empty>'}"
                    f"{inner_html or '<empty>'}"
                )

            inner_html = get_inner_html_safely()
            body_text = get_text_safely()

        snippet = body_text[:500].replace("\n", " ")

        if not body_text.startswith("{") and not body_text.startswith("["):
            self.fail(
                f"Expected JSON content but got non-JSON text at {self.driver.current_url}: "
                f"{snippet or '<empty>'}"
                f"{inner_html or '<empty>'}"
            )

        try:
            body_json = loads(body_text)
        except JSONDecodeError as e:
            self.fail(
                f"Expected JSON but got invalid content at {self.driver.current_url}: "
                f"{snippet or '<empty>'}"
                f"{inner_html or '<empty>'}"
                f"(JSON error: {e})"
            )

        return body_json

    def get_shadow_root(
        self, selector: str, container: WebElement | WebDriver | None = None, timeout: float = 10
    ) -> WebElement:
        """Get the shadow root of a web component specified by `selector`."""
        if not container:
            container = self.driver
        wait = WebDriverWait(container, timeout)
        host: WebElement | None = None

        try:
            host = wait.until(lambda c: c.find_element(By.CSS_SELECTOR, selector))
        except TimeoutException:
            self.fail(f"Timed out waiting for shadow host {selector} to appear")

        attempts = 0

        while attempts < SHADOW_ROOT_RETRIES:
            try:
                host = container.find_element(By.CSS_SELECTOR, selector)
                return host.shadow_root
            except (
                NoSuchElementException,
                NoSuchShadowRootException,
                DetachedShadowRootException,
                StaleElementReferenceException,
            ):
                attempts += 1
                sleep(0.2)

        inner_html = "<no host>"
        if host is not None:
            try:
                inner_html = host.get_attribute("innerHTML") or "<no host>"
            except (DetachedShadowRootException, StaleElementReferenceException):
                inner_html = "<stale host>"

        raise RuntimeError(
            f"Failed to obtain shadow root for {selector} after {attempts} attempts. "
            f"Host innerHTML: {inner_html}"
        )

    def shady_dom(self) -> WebElement:
        class wrapper:
            def __init__(self, container: WebDriver):
                self.container = container

            def find_element(self, by: str, selector: str) -> WebElement:
                return self.container.execute_script(
                    "return document.__shady_native_querySelector(arguments[0])", selector
                )

        return wrapper(self.driver)

    def login(self, shadow_dom=True):
        """Perform the entire authentik login flow."""

        if shadow_dom:
            flow_executor = self.get_shadow_root("ak-flow-executor")
            identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        else:
            flow_executor = self.shady_dom()
            identification_stage = self.shady_dom()

        wait = WebDriverWait(identification_stage, self.wait_timeout)
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=uidField]")))

        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").click()
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").send_keys(
            self.user.username
        )
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").send_keys(
            Keys.ENTER
        )

        if shadow_dom:
            flow_executor = self.get_shadow_root("ak-flow-executor")
            password_stage = self.get_shadow_root("ak-stage-password", flow_executor)
        else:
            flow_executor = self.shady_dom()
            password_stage = self.shady_dom()

        wait = WebDriverWait(password_stage, self.wait_timeout)
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=password]")))

        password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(
            self.user.username
        )
        password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(Keys.ENTER)
        sleep(1)

    def assert_user(self, expected_user: User):
        """Check users/me API and assert it matches expected_user"""

        expected_url = self.url("authentik_api:user-me") + "?format=json"
        self.driver.get(expected_url)

        self.wait.until(lambda d: d.current_url == expected_url)

        user_json = self.parse_json_content()
        data = user_json.get("user")
        snippet = dumps(user_json, indent=2)[:500].replace("\n", " ")

        self.assertIsNotNone(
            data,
            f"Missing 'user' key in response at {self.driver.current_url}: {snippet}",
        )

        user = UserSerializer(data=data)

        user.is_valid()

        self.assertEqual(
            user["username"].value,
            expected_user.username,
            f"Username mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            user["name"].value,
            expected_user.name,
            f"Name mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            user["email"].value,
            expected_user.email,
            f"Email mismatch at {self.driver.current_url}: {snippet}",
        )


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
