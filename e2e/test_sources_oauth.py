"""test OAuth Source"""
from os.path import abspath
from sys import platform
from typing import Any, Dict, Optional
from unittest.case import skipUnless

from docker.models.containers import Container
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from structlog import get_logger
from yaml import safe_dump

from e2e.utils import SeleniumTestCase
from passbook.flows.models import Flow
from passbook.providers.oauth2.generators import generate_client_secret
from passbook.sources.oauth.models import OAuthSource

TOKEN_URL = "http://127.0.0.1:5556/dex/token"
CONFIG_PATH = "/tmp/dex.yml"
LOGGER = get_logger()


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceOAuth(SeleniumTestCase):
    """test OAuth Source flow"""

    container: Container

    def setUp(self):
        self.client_secret = generate_client_secret()
        self.prepare_dex_config()
        super().setUp()

    def prepare_dex_config(self):
        """Since Dex does not document which environment
        variables can be used to configure clients"""
        config = {
            "enablePasswordDB": True,
            "issuer": "http://127.0.0.1:5556/dex",
            "logger": {"level": "debug"},
            "staticClients": [
                {
                    "id": "example-app",
                    "name": "Example App",
                    "redirectURIs": [
                        self.url(
                            "passbook_sources_oauth:oauth-client-callback",
                            source_slug="dex",
                        )
                    ],
                    "secret": self.client_secret,
                }
            ],
            "staticPasswords": [
                {
                    "email": "admin@example.com",
                    # hash for password
                    "hash": "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W",
                    "userID": "08a8684b-db88-4b73-90a9-3cd1661f5466",
                    "username": "admin",
                }
            ],
            "storage": {"config": {"file": "/tmp/dex.db"}, "type": "sqlite3"},
            "web": {"http": "0.0.0.0:5556"},
        }
        with open(CONFIG_PATH, "w+") as _file:
            safe_dump(config, _file)

    def get_container_specs(self) -> Optional[Dict[str, Any]]:
        return {
            "image": "quay.io/dexidp/dex:v2.24.0",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
            "command": "serve /config.yml",
            "healthcheck": Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:5556/dex/healthz"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            "volumes": {abspath(CONFIG_PATH): {"bind": "/config.yml", "mode": "ro"}},
        }

    def create_objects(self):
        """Create required objects"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")

        OAuthSource.objects.create(
            name="dex",
            slug="dex",
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            provider_type="openid-connect",
            authorization_url="http://127.0.0.1:5556/dex/auth",
            access_token_url=TOKEN_URL,
            profile_url="http://127.0.0.1:5556/dex/userinfo",
            consumer_key="example-app",
            consumer_secret=self.client_secret,
        )

    def test_oauth_enroll(self):
        """test OAuth Source With With OIDC"""
        self.create_objects()
        self.driver.get(self.live_server_url)

        self.wait.until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "pf-c-login__main-footer-links-item-link")
            )
        )
        self.driver.find_element(
            By.CLASS_NAME, "pf-c-login__main-footer-links-item-link"
        ).click()

        # Now we should be at the IDP, wait for the login field
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))
        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        # At this point we've been redirected back
        # and we're asked for the username
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "username").send_keys("foo")
        self.driver.find_element(By.NAME, "username").send_keys(Keys.ENTER)

        # Wait until we've loaded the user info page
        self.wait.until(ec.presence_of_element_located((By.LINK_TEXT, "foo")))
        self.driver.find_element(By.LINK_TEXT, "foo").click()

        self.wait_for_url(self.url("passbook_core:user-settings"))
        self.assertEqual(
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"), "admin",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "admin@example.com",
        )

    def test_oauth_enroll_auth(self):
        """test OAuth Source With With OIDC (enroll and authenticate again)"""
        self.test_oauth_enroll()
        # We're logged in at the end of this, log out and re-login
        self.driver.find_element(By.CSS_SELECTOR, "[aria-label=logout]").click()

        self.wait.until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "pf-c-login__main-footer-links-item-link")
            )
        )
        self.driver.find_element(
            By.CLASS_NAME, "pf-c-login__main-footer-links-item-link"
        ).click()

        # Now we should be at the IDP, wait for the login field
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))
        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        # Wait until we've loaded the user info page
        self.wait.until(ec.presence_of_element_located((By.LINK_TEXT, "foo")))
        self.driver.find_element(By.LINK_TEXT, "foo").click()

        self.wait_for_url(self.url("passbook_core:user-settings"))
        self.assertEqual(
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"), "admin",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "admin@example.com",
        )
