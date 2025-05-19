"""authentik e2e testing utilities"""

# This file cannot import anything django or anything that will load django

import json
from sys import stderr
from time import sleep
from typing import TYPE_CHECKING
from unittest.case import TestCase
from urllib.parse import urlencode

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from structlog.stdlib import get_logger

from tests import IS_CI, RETRIES, get_local_ip
from tests.websocket import BaseWebsocketTestCase

if TYPE_CHECKING:
    from authentik.core.models import User


class BaseSeleniumTestCase(TestCase):
    """Mixin which adds helpers for spinning up Selenium"""

    host = get_local_ip()
    wait_timeout: int
    user: "User"

    def setUp(self):
        if IS_CI:
            print("::group::authentik Logs", file=stderr)
        from django.apps import apps

        from authentik.core.tests.utils import create_test_admin_user

        apps.get_app_config("authentik_tenants").ready()
        self.wait_timeout = 60
        self.driver = self._get_driver()
        self.driver.implicitly_wait(30)
        self.wait = WebDriverWait(self.driver, self.wait_timeout)
        self.logger = get_logger()
        self.user = create_test_admin_user()
        super().setUp()

    def _get_driver(self) -> WebDriver:
        count = 0
        try:
            opts = webdriver.ChromeOptions()
            opts.add_argument("--disable-search-engine-choice-screen")
            return webdriver.Chrome(options=opts)
        except WebDriverException:
            pass
        while count < RETRIES:
            try:
                driver = webdriver.Remote(
                    command_executor="http://localhost:4444/wd/hub",
                    options=webdriver.ChromeOptions(),
                )
                driver.maximize_window()
                return driver
            except WebDriverException:
                count += 1
        raise ValueError(f"Webdriver failed after {RETRIES}.")

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

    def wait_for_url(self, desired_url):
        """Wait until URL is `desired_url`."""
        self.wait.until(
            lambda driver: driver.current_url == desired_url,
            f"URL {self.driver.current_url} doesn't match expected URL {desired_url}",
        )

    def url(self, view, query: dict | None = None, **kwargs) -> str:
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

    def get_shadow_root(
        self, selector: str, container: WebElement | WebDriver | None = None
    ) -> WebElement:
        """Get shadow root element's inner shadowRoot"""
        if not container:
            container = self.driver
        shadow_root = container.find_element(By.CSS_SELECTOR, selector)
        element = self.driver.execute_script("return arguments[0].shadowRoot", shadow_root)
        return element

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
        """Do entire login flow"""

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

    def assert_user(self, expected_user: "User"):
        """Check users/me API and assert it matches expected_user"""
        from authentik.core.api.users import UserSerializer

        self.driver.get(self.url("authentik_api:user-me") + "?format=json")
        user_json = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        user = UserSerializer(data=json.loads(user_json)["user"])
        user.is_valid()
        self.assertEqual(user["username"].value, expected_user.username)
        self.assertEqual(user["name"].value, expected_user.name)
        self.assertEqual(user["email"].value, expected_user.email)


class SeleniumTestCase(BaseSeleniumTestCase, StaticLiveServerTestCase):
    """Test case which spins up a selenium instance and a HTTP-only test server"""


class WebsocketSeleniumTestCase(BaseSeleniumTestCase, BaseWebsocketTestCase):
    """Test case which spins up a selenium instance and a Websocket/HTTP test server"""
