"""test OAuth Source"""
from os.path import abspath
from sys import platform
from time import sleep
from typing import Any, Dict, Optional
from unittest.case import skipUnless

from django.test import override_settings
from docker.models.containers import Container
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from structlog import get_logger
from yaml import safe_dump

from e2e.utils import SeleniumTestCase, retry
from passbook.flows.models import Flow
from passbook.providers.oauth2.generators import (
    generate_client_id,
    generate_client_secret,
)
from passbook.sources.oauth.models import OAuthSource

CONFIG_PATH = "/tmp/dex.yml"
LOGGER = get_logger()


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceOAuth2(SeleniumTestCase):
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

        OAuthSource.objects.create(  # nosec
            name="dex",
            slug="dex",
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            provider_type="openid-connect",
            authorization_url="http://127.0.0.1:5556/dex/auth",
            access_token_url="http://127.0.0.1:5556/dex/token",
            profile_url="http://127.0.0.1:5556/dex/userinfo",
            consumer_key="example-app",
            consumer_secret=self.client_secret,
        )

    @retry()
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

        self.wait.until(ec.presence_of_element_located((By.NAME, "username")))
        # At this point we've been redirected back
        # and we're asked for the username
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "username").send_keys("foo")
        self.driver.find_element(By.NAME, "username").send_keys(Keys.ENTER)

        # Wait until we've loaded the user info page
        self.wait.until(ec.presence_of_element_located((By.ID, "user-settings")))
        self.driver.get(self.url("passbook_core:user-settings"))

        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"),
            "admin",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "admin@example.com",
        )

    @retry()
    @override_settings(SESSION_COOKIE_SAMESITE="strict")
    def test_oauth_samesite_strict(self):
        """test OAuth Source With SameSite set to strict
        (=will fail because session is not carried over)"""
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

        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-alert__title"))
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, ".pf-c-alert__title").text,
            "Authentication Failed.",
        )

    @retry()
    def test_oauth_enroll_auth(self):
        """test OAuth Source With With OIDC (enroll and authenticate again)"""
        self.test_oauth_enroll()
        # We're logged in at the end of this, log out and re-login
        self.driver.find_element(By.ID, "logout").click()

        self.wait.until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "pf-c-login__main-footer-links-item-link")
            )
        )
        sleep(1)
        self.driver.find_element(
            By.CLASS_NAME, "pf-c-login__main-footer-links-item-link"
        ).click()
        sleep(1)
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

        self.wait.until(ec.presence_of_element_located((By.ID, "user-settings")))
        self.driver.get(self.url("passbook_core:user-settings"))

        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"),
            "admin",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "admin@example.com",
        )


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceOAuth1(SeleniumTestCase):
    """Test OAuth1 Source"""

    def setUp(self) -> None:
        self.client_id = generate_client_id()
        self.client_secret = generate_client_secret()
        self.source_slug = "oauth1-test"
        super().setUp()

    def get_container_specs(self) -> Optional[Dict[str, Any]]:
        return {
            "image": "docker.beryju.org/proxy/beryju/oauth1-test-server",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
            "environment": {
                "OAUTH1_CLIENT_ID": self.client_id,
                "OAUTH1_CLIENT_SECRET": self.client_secret,
                "OAUTH1_REDIRECT_URI": (
                    self.url(
                        "passbook_sources_oauth:oauth-client-callback",
                        source_slug=self.source_slug,
                    )
                ),
            },
        }

    def create_objects(self):
        """Create required objects"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")

        OAuthSource.objects.create(  # nosec
            name="oauth1",
            slug=self.source_slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            provider_type="twitter",
            request_token_url="http://localhost:5000/oauth/request_token",
            access_token_url="http://localhost:5000/oauth/access_token",
            authorization_url="http://localhost:5000/oauth/authorize",
            profile_url="http://localhost:5000/api/me",
            consumer_key=self.client_id,
            consumer_secret=self.client_secret,
        )

    @retry()
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
        self.wait.until(ec.presence_of_element_located((By.NAME, "username")))
        self.driver.find_element(By.NAME, "username").send_keys("example-user")
        self.driver.find_element(By.NAME, "username").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "[name='confirm']"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[name='confirm']").click()

        # Wait until we've loaded the user info page
        sleep(2)
        self.wait.until(ec.presence_of_element_located((By.ID, "user-settings")))
        self.driver.get(self.url("passbook_core:user-settings"))

        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text,
            "example-user",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"),
            "example-user",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"),
            "test name",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "foo@example.com",
        )
