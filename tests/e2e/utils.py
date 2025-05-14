"""authentik e2e testing utilities"""

import json
import os
import socket
from collections.abc import Callable
from functools import lru_cache, wraps
from os import environ
from sys import stderr
from time import sleep
from typing import Any
from unittest.case import TestCase
from urllib.parse import urlencode

from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test.testcases import TransactionTestCase
from django.urls import reverse
from docker import DockerClient, from_env
from docker.errors import DockerException
from docker.models.containers import Container
from docker.models.networks import Network
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from structlog.stdlib import get_logger

from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id

RETRIES = int(environ.get("RETRIES", "3"))
IS_CI = "CI" in environ


def get_docker_tag() -> str:
    """Get docker-tag based off of CI variables"""
    env_pr_branch = "GITHUB_HEAD_REF"
    default_branch = "GITHUB_REF"
    branch_name = os.environ.get(default_branch, "main")
    if os.environ.get(env_pr_branch, "") != "":
        branch_name = os.environ[env_pr_branch]
    branch_name = branch_name.replace("refs/heads/", "").replace("/", "-")
    return f"gh-{branch_name}"


def get_local_ip() -> str:
    """Get the local machine's IP"""
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)
    return ip_addr


class DockerTestCase(TestCase):
    """Mixin for dealing with containers"""

    max_healthcheck_attempts = 30

    __client: DockerClient
    __network: Network

    __label_id = generate_id()

    def setUp(self) -> None:
        self.__client = from_env()
        self.__network = self.docker_client.networks.create(name=f"authentik-test-{generate_id()}")

    @property
    def docker_client(self) -> DockerClient:
        return self.__client

    @property
    def docker_network(self) -> Network:
        return self.__network

    @property
    def docker_labels(self) -> dict:
        return {"io.goauthentik.test": self.__label_id}

    def wait_for_container(self, container: Container):
        """Check that container is health"""
        attempt = 0
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)
            attempt += 1
            if attempt >= self.max_healthcheck_attempts:
                self.failureException("Container failed to start")

    def get_container_image(self, base: str) -> str:
        """Try to pull docker image based on git branch, fallback to main if not found."""
        image = f"{base}:gh-main"
        try:
            branch_image = f"{base}:{get_docker_tag()}"
            self.docker_client.images.pull(branch_image)
            return branch_image
        except DockerException:
            self.docker_client.images.pull(image)
        return image

    def run_container(self, **specs: dict[str, Any]) -> Container:
        if "network_mode" not in specs:
            specs["network"] = self.__network.name
        specs["labels"] = self.docker_labels
        specs["detach"] = True
        if hasattr(self, "live_server_url"):
            specs.setdefault("environment", {})
            specs["environment"]["AUTHENTIK_HOST"] = self.live_server_url
        container = self.docker_client.containers.run(**specs)
        container.reload()
        state = container.attrs.get("State", {})
        if "Health" not in state:
            return container
        self.wait_for_container(container)
        return container

    def output_container_logs(self, container: Container | None = None):
        """Output the container logs to our STDOUT"""
        if IS_CI:
            image = container.image
            tags = image.tags[0] if len(image.tags) > 0 else str(image)
            print(f"::group::Container logs - {tags}")
        for log in container.logs().decode().split("\n"):
            print(log)
        if IS_CI:
            print("::endgroup::")

    def tearDown(self):
        containers: list[Container] = self.docker_client.containers.list(
            filters={"label": ",".join(f"{x}={y}" for x, y in self.docker_labels.items())}
        )
        for container in containers:
            self.output_container_logs(container)
            try:
                container.kill()
            except DockerException:
                pass
            try:
                container.remove(force=True)
            except DockerException:
                pass
        self.__network.remove()


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

    def login(self):
        """Do entire login flow"""
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)

        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").click()
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").send_keys(
            self.user.username
        )
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").send_keys(
            Keys.ENTER
        )

        flow_executor = self.get_shadow_root("ak-flow-executor")
        password_stage = self.get_shadow_root("ak-stage-password", flow_executor)
        password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(
            self.user.username
        )
        password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(Keys.ENTER)
        sleep(1)

    def assert_user(self, expected_user: User):
        """Check users/me API and assert it matches expected_user"""
        self.driver.get(self.url("authentik_api:user-me") + "?format=json")
        user_json = self.driver.find_element(By.CSS_SELECTOR, "pre").text
        user = UserSerializer(data=json.loads(user_json)["user"])
        user.is_valid()
        self.assertEqual(user["username"].value, expected_user.username)
        self.assertEqual(user["name"].value, expected_user.name)
        self.assertEqual(user["email"].value, expected_user.email)


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
