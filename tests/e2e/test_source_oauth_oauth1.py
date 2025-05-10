"""test OAuth Source"""

from time import sleep
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.crypto.generators import generate_id, generate_key
from authentik.flows.models import Flow
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, retry


class OAuth1Callback(OAuthCallback):
    """OAuth1 Callback with custom getters"""

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("id")


@registry.register()
class OAUth1Type(SourceType):
    """OAuth1 Type definition"""

    callback_view = OAuth1Callback
    verbose_name = "OAuth1"
    name = "oauth1"

    request_token_url = "http://localhost:5001/oauth/request_token"  # nosec
    access_token_url = "http://localhost:5001/oauth/access_token"  # nosec
    authorization_url = "http://localhost:5001/oauth/authorize"
    profile_url = "http://localhost:5001/api/me"
    urls_customizable = False

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("screen_name"),
            "email": info.get("email"),
            "name": info.get("name"),
        }


class TestSourceOAuth1(SeleniumTestCase):
    """Test OAuth1 Source"""

    def setUp(self) -> None:
        self.client_id = generate_id()
        self.client_secret = generate_key()
        self.source_slug = generate_id()
        super().setUp()
        self.run_container(
            image="ghcr.io/beryju/oauth1-test-server:v1.1",
            ports={"5000": "5001"},
            environment={
                "OAUTH1_CLIENT_ID": self.client_id,
                "OAUTH1_CLIENT_SECRET": self.client_secret,
                "OAUTH1_REDIRECT_URI": self.url(
                    "authentik_sources_oauth:oauth-client-callback",
                    source_slug=self.source_slug,
                ),
            },
        )

    def create_objects(self):
        """Create required objects"""
        # Bootstrap all needed objects
        authentication_flow = Flow.objects.get(slug="default-source-authentication")
        enrollment_flow = Flow.objects.get(slug="default-source-enrollment")

        source = OAuthSource.objects.create(  # nosec
            name=generate_id(),
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
        self.wait_for_url(self.if_user_url())

        self.assert_user(User(username="example-user", name="test name", email="foo@example.com"))
