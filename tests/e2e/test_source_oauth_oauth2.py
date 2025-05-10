"""test OAuth Source"""

from json import loads
from pathlib import Path
from time import sleep

from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.crypto.generators import generate_id
from authentik.flows.models import Flow
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, retry


class TestSourceOAuth2(SeleniumTestCase):
    """test OAuth Source flow"""

    def setUp(self):
        self.client_secret = generate_id()
        self.slug = generate_id()
        super().setUp()
        self.run_container(
            image="ghcr.io/dexidp/dex:v2.28.1",
            ports={"5556": "5556"},
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:5556/dex/healthz"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            environment={
                "AK_REDIRECT_URL": self.url(
                    "authentik_sources_oauth:oauth-client-callback",
                    source_slug=self.slug,
                ),
                "AK_CLIENT_SECRET": self.client_secret,
            },
            volumes={
                f"{Path(__file__).parent / "sources_oauth2_dex" / "dex.yaml"}": {
                    "bind": "/etc/dex/config.docker.yaml",
                }
            },
        )

    def create_objects(self):
        """Create required objects"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")

        source = OAuthSource.objects.create(  # nosec
            name=generate_id(),
            slug=self.slug,
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
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-source-authentication.yaml",
        "default/flow-default-source-enrollment.yaml",
        "default/flow-default-source-pre-authentication.yaml",
    )
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
        self.wait_for_url(self.if_user_url())

        self.assert_user(User(username="foo", name="admin", email="admin@example.com"))

    @retry()
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
        self.wait_for_url(self.if_user_url())

        self.assert_user(User(username="foo", name="admin", email="admin@example.com"))

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-source-authentication.yaml",
        "default/flow-default-source-enrollment.yaml",
        "default/flow-default-source-pre-authentication.yaml",
    )
    def test_oauth_link(self):
        """test OAuth Source link OIDC"""
        self.create_objects()
        self.driver.get(self.live_server_url)
        self.login()

        self.driver.get(
            self.url("authentik_sources_oauth:oauth-client-login", source_slug=self.slug)
        )

        # Now we should be at the IDP, wait for the login field
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))
        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        # Wait until we're logged in
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]")))
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        self.driver.get(self.url("authentik_api:usersourceconnection-list") + "?format=json")
        body_json = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)
        results = body_json["results"]
        self.assertEqual(len(results), 1)
        connection = results[0]
        self.assertEqual(connection["source_obj"]["slug"], self.slug)
        self.assertEqual(connection["user"], self.user.pk)
