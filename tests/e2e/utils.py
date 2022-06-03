"""authentik e2e testing utilities"""
import json
import os
from functools import lru_cache, wraps
from os import environ, makedirs
from time import sleep, time
from typing import Any, Callable, Optional

from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.operations.special import RunPython
from django.test.testcases import TransactionTestCase
from django.urls import reverse
from docker import DockerClient, from_env
from docker.errors import DockerException
from docker.models.containers import Container
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from structlog.stdlib import get_logger

from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.managed.manager import ObjectManager

RETRIES = int(environ.get("RETRIES", "3"))


def get_docker_tag() -> str:
    """Get docker-tag based off of CI variables"""
    env_pr_branch = "GITHUB_HEAD_REF"
    default_branch = "GITHUB_REF"
    branch_name = os.environ.get(default_branch, "main")
    if os.environ.get(env_pr_branch, "") != "":
        branch_name = os.environ[env_pr_branch]
    branch_name = branch_name.replace("refs/heads/", "").replace("/", "-")
    return f"gh-{branch_name}"


class SeleniumTestCase(StaticLiveServerTestCase):
    """StaticLiveServerTestCase which automatically creates a Webdriver instance"""

    container: Optional[Container] = None
    wait_timeout: int
    user: User

    def setUp(self):
        super().setUp()
        # pylint: disable=invalid-name
        self.maxDiff = None
        self.wait_timeout = 60
        self.driver = self._get_driver()
        self.driver.maximize_window()
        self.driver.implicitly_wait(30)
        self.wait = WebDriverWait(self.driver, self.wait_timeout)
        self.logger = get_logger()
        self.user = create_test_admin_user()
        if specs := self.get_container_specs():
            self.container = self._start_container(specs)

    def get_container_image(self, base: str) -> str:
        """Try to pull docker image based on git branch, fallback to main if not found."""
        client: DockerClient = from_env()
        image = f"{base}:gh-main"
        try:
            branch_image = f"{base}:{get_docker_tag()}"
            client.images.pull(branch_image)
            return branch_image
        except DockerException:
            client.images.pull(image)
        return image

    def _start_container(self, specs: dict[str, Any]) -> Container:
        client: DockerClient = from_env()
        container = client.containers.run(**specs)
        if "healthcheck" not in specs:
            return container
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            self.logger.info("Container failed healthcheck")
            sleep(1)

    def output_container_logs(self, container: Optional[Container] = None):
        """Output the container logs to our STDOUT"""
        _container = container or self.container
        print(f"--------container logs {_container.image.tags[0]}")
        for log in _container.logs().decode().split("\n"):
            print(log)
        print(f"--------end container logs {_container.image.tags[0]}")

    def get_container_specs(self) -> Optional[dict[str, Any]]:
        """Optionally get container specs which will launched on setup, wait for the container to
        be healthy, and deleted again on tearDown"""
        return None

    def _get_driver(self) -> WebDriver:
        count = 0
        while count < RETRIES:
            try:
                return webdriver.Remote(
                    command_executor="http://localhost:4444/wd/hub",
                    options=webdriver.ChromeOptions(),
                )
            except WebDriverException:
                count += 1
        raise ValueError(f"Webdriver failed after {RETRIES}.")

    def tearDown(self):
        if "TF_BUILD" in environ:
            makedirs("selenium_screenshots/", exist_ok=True)
            screenshot_file = f"selenium_screenshots/{self.__class__.__name__}_{time()}.png"
            self.driver.save_screenshot(screenshot_file)
            self.logger.warning("Saved screenshot", file=screenshot_file)
        self.logger.debug("--------browser logs")
        for line in self.driver.get_log("browser"):
            self.logger.debug(line["message"], source=line["source"], level=line["level"])
        self.logger.debug("--------end browser logs")
        if self.container:
            self.output_container_logs()
            self.container.kill()
        self.driver.quit()
        super().tearDown()

    def wait_for_url(self, desired_url):
        """Wait until URL is `desired_url`."""
        self.wait.until(
            lambda driver: driver.current_url == desired_url,
            f"URL {self.driver.current_url} doesn't match expected URL {desired_url}",
        )

    def url(self, view, **kwargs) -> str:
        """reverse `view` with `**kwargs` into full URL using live_server_url"""
        return self.live_server_url + reverse(view, kwargs=kwargs)

    def if_user_url(self, view) -> str:
        """same as self.url() but show URL in shell"""
        return f"{self.live_server_url}/if/user/#{view}"

    def get_shadow_root(self, selector: str, container: Optional[WebElement] = None) -> WebElement:
        """Get shadow root element's inner shadowRoot"""
        if not container:
            container = self.driver
        shadow_root = container.find_element(By.CSS_SELECTOR, selector)
        element = self.driver.execute_script("return arguments[0].shadowRoot", shadow_root)
        return element

    def login(self):
        """Do entire login flow and check user afterwards"""
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


def apply_migration(app_name: str, migration_name: str):
    """Re-apply migrations that create objects using RunPython before test cases"""

    def wrapper_outter(func: Callable):
        """Retry test multiple times"""

        @wraps(func)
        def wrapper(self: TransactionTestCase, *args, **kwargs):
            migration = get_loader().get_migration(app_name, migration_name)
            with connection.schema_editor() as schema_editor:
                for operation in migration.operations:
                    if not isinstance(operation, RunPython):
                        continue
                    operation.code(apps, schema_editor)
            return func(self, *args, **kwargs)

        return wrapper

    return wrapper_outter


def object_manager(func: Callable):
    """Run objectmanager before a test function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Run objectmanager before a test function"""
        ObjectManager().run()
        return func(*args, **kwargs)

    return wrapper


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
            # pylint: disable=catching-non-exception
            except tuple(exceptions) as exc:
                count += 1
                if count > max_retires:
                    logger.debug("Exceeded retry count", exc=exc, test=self)
                    # pylint: disable=raising-non-exception
                    raise exc
                logger.debug("Retrying on error", exc=exc, test=self)
                self.tearDown()
                self._post_teardown()  # noqa
                self.setUp()
                return wrapper(self, *args, **kwargs)

        return wrapper

    return retry_actual
