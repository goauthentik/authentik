"""test OAuth Source"""
from os.path import abspath
from sys import platform
from time import sleep
from typing import Any, Optional
from unittest.case import skipUnless

from docker.models.containers import Container
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from yaml import safe_dump

from authentik.core.models import User
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, apply_migration, object_manager, retry

CONFIG_PATH = "/tmp/dex.yml"  # nosec


class OAUth1Callback(OAuthCallback):
    """OAuth1 Callback with custom getters"""

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("id")

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("screen_name"),
            "email": info.get("email"),
            "name": info.get("name"),
        }


@MANAGER.type()
class OAUth1Type(SourceType):
    """OAuth1 Type definition"""

    callback_view = OAUth1Callback
    name = "OAuth1"
    slug = "oauth1"

    request_token_url = "http://localhost:5000/oauth/request_token"  # nosec
    access_token_url = "http://localhost:5000/oauth/access_token"  # nosec
    authorization_url = "http://localhost:5000/oauth/authorize"
    profile_url = "http://localhost:5000/api/me"
    urls_customizable = False


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceOAuth2(SeleniumTestCase):
    """test OAuth Source flow"""

    container: Container

    def setUp(self):
        self.client_secret = generate_key()
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
                            "authentik_sources_oauth:oauth-client-callback",
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
            "storage": {"config": {"file": "/tmp/dex.db"}, "type": "sqlite3"},  # nosec
            "web": {"http": "0.0.0.0:5556"},
        }
        with open(CONFIG_PATH, "w+", encoding="utf8") as _file:
            safe_dump(config, _file)

    def get_container_specs(self) -> Optional[dict[str, Any]]:
        return {
            "image": "ghcr.io/dexidp/dex:v2.28.1",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
            "command": "dex serve /config.yml",
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

        source = OAuthSource.objects.create(  # nosec
            name="dex",
            slug="dex",
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            provider_type="openidconnect",
            authorization_url="http://127.0.0.1:5556/dex/auth",
            access_token_url="http://127.0.0.1:5556/dex/token",
            profile_url="http://127.0.0.1:5556/dex/userinfo",
            consumer_key="example-app",
            consumer_secret=self.client_secret,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

    @retry()
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0009_source_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    @object_manager
    def test_oauth_enroll(self):
        """test OAuth Source With With OIDC"""
        self.create_objects()
        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the login field
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))
        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]")))
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        # At this point we've been redirected back
        # and we're asked for the username
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)

        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").click()
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys("foo")
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys(Keys.ENTER)

        # Wait until we've logged in
        self.wait_for_url(self.if_user_url("/library"))
        self.driver.get(self.if_user_url("/settings"))

        self.assert_user(User(username="foo", name="admin", email="admin@example.com"))

    @retry()
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0009_source_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    @object_manager
    def test_oauth_enroll_auth(self):
        """test OAuth Source With With OIDC (enroll and authenticate again)"""
        self.test_oauth_enroll()
        # We're logged in at the end of this, log out and re-login
        self.driver.get(self.url("authentik_flows:default-invalidation"))
        sleep(1)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the login field
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))
        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]")))
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        # Wait until we've logged in
        self.wait_for_url(self.if_user_url("/library"))
        self.driver.get(self.if_user_url("/settings"))

        self.assert_user(User(username="foo", name="admin", email="admin@example.com"))


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceOAuth1(SeleniumTestCase):
    """Test OAuth1 Source"""

    def setUp(self) -> None:
        self.client_id = generate_id()
        self.client_secret = generate_key()
        self.source_slug = "oauth1-test"
        super().setUp()

    def get_container_specs(self) -> Optional[dict[str, Any]]:
        return {
            "image": "ghcr.io/beryju/oauth1-test-server:latest",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
            "environment": {
                "OAUTH1_CLIENT_ID": self.client_id,
                "OAUTH1_CLIENT_SECRET": self.client_secret,
                "OAUTH1_REDIRECT_URI": (
                    self.url(
                        "authentik_sources_oauth:oauth-client-callback",
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

        source = OAuthSource.objects.create(  # nosec
            name="oauth1",
            slug=self.source_slug,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            provider_type="oauth1",
            consumer_key=self.client_id,
            consumer_secret=self.client_secret,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()

    @retry()
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0009_source_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    @object_manager
    def test_oauth_enroll(self):
        """test OAuth Source With With OIDC"""
        self.create_objects()
        self.driver.get(self.live_server_url)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button")
            )
        )
        identification_stage.find_element(
            By.CSS_SELECTOR, ".pf-c-login__main-footer-links-item > button"
        ).click()

        # Now we should be at the IDP, wait for the login field
        self.wait.until(ec.presence_of_element_located((By.NAME, "username")))
        self.driver.find_element(By.NAME, "username").send_keys("example-user")
        self.driver.find_element(By.NAME, "username").send_keys(Keys.ENTER)
        sleep(2)

        # Wait until we're logged in
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "[name='confirm']")))
        self.driver.find_element(By.CSS_SELECTOR, "[name='confirm']").click()

        # Wait until we've loaded the user info page
        sleep(2)
        # Wait until we've logged in
        self.wait_for_url(self.if_user_url("/library"))
        self.driver.get(self.if_user_url("/settings"))

        self.assert_user(User(username="example-user", name="test name", email="foo@example.com"))
