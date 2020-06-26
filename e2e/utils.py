"""passbook e2e testing utilities"""
from functools import lru_cache
from glob import glob
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers, isfunction
from os import makedirs
from time import time

from Cryptodome.PublicKey import RSA
from django.apps import apps
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection, transaction
from django.db.utils import IntegrityError
from django.shortcuts import reverse
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from structlog import get_logger

from passbook.core.models import User


@lru_cache
# pylint: disable=invalid-name
def USER() -> User:  # noqa
    """Cached function that always returns pbadmin"""
    return User.objects.get(username="pbadmin")


def ensure_rsa_key():
    """Ensure that at least one RSAKey Object exists, create one if none exist"""
    from oidc_provider.models import RSAKey

    if not RSAKey.objects.exists():
        key = RSA.generate(2048)
        rsakey = RSAKey(key=key.exportKey("PEM").decode("utf8"))
        rsakey.save()


class SeleniumTestCase(StaticLiveServerTestCase):
    """StaticLiveServerTestCase which automatically creates a Webdriver instance"""

    def setUp(self):
        super().setUp()
        makedirs("out", exist_ok=True)
        self.driver = self._get_driver()
        self.driver.maximize_window()
        self.driver.implicitly_wait(60)
        self.wait = WebDriverWait(self.driver, 120)
        self.apply_default_data()
        self.logger = get_logger()

    def _get_driver(self) -> WebDriver:
        return webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME,
        )

    def tearDown(self):
        self.driver.save_screenshot(f"out/{self.__class__.__name__}_{time()}.png")
        for line in self.driver.get_log("browser"):
            self.logger.warning(
                line["message"], source=line["source"], level=line["level"]
            )
        self.driver.quit()
        super().tearDown()

    def wait_for_url(self, desired_url):
        """Wait until URL is `desired_url`."""
        self.wait.until(lambda driver: driver.current_url == desired_url)

    def url(self, view, **kwargs) -> str:
        """reverse `view` with `**kwargs` into full URL using live_server_url"""
        return self.live_server_url + reverse(view, kwargs=kwargs)

    def apply_default_data(self):
        """apply objects created by migrations after tables have been truncated"""
        # Find all migration files
        # load all functions
        migration_files = glob("**/migrations/*.py", recursive=True)
        matches = []
        for migration in migration_files:
            with open(migration, "r+") as migration_file:
                # Check if they have a `RunPython`
                if "RunPython" in migration_file.read():
                    matches.append(migration)

        with connection.schema_editor() as schema_editor:
            for match in matches:
                # Load module from file path
                spec = spec_from_file_location("", match)
                migration_module = module_from_spec(spec)
                # pyright: reportGeneralTypeIssues=false
                spec.loader.exec_module(migration_module)
                # Call all functions from module
                for _, func in getmembers(migration_module, isfunction):
                    with transaction.atomic():
                        try:
                            func(apps, schema_editor)
                        except IntegrityError:
                            pass
