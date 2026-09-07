"""Shared tooling for OAuth source e2e tests"""

from pathlib import Path
from time import sleep
from urllib.parse import urlsplit, urlunsplit

from docker.types import Healthcheck
from selenium.common.exceptions import (
    DetachedShadowRootException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import SourceUserMatchingModes, User
from authentik.core.tests.utils import create_test_user
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage
from tests.decorators import SHADOW_ROOT_RETRIES, retry

APP_URL = "http://localhost:9009"
# A non-root app URL, to check the original destination survives the source login
DEEP_LINK_URL = f"{APP_URL}/deep/link"


def initial_uri(entry: str) -> str:
    """The request URI an app sees when a login is started at `entry`"""
    parts = urlsplit(entry)
    return urlunsplit(("", "", parts.path or "/", parts.query, "")) or "/"


class FlowStageMixin:
    """Reach into the flow executor's shadow DOM"""

    def get_stage_shadow_root(self, stage: str):
        """Dive to a flow stage's shadow root.

        Right after a redirect the executor can still be swapping stages, which
        detaches the outer shadow root part-way through the two-step dive.
        """
        for attempt in range(SHADOW_ROOT_RETRIES):
            try:
                flow_executor = self.get_shadow_root("ak-flow-executor")
                return self.get_shadow_root(stage, flow_executor)
            except DetachedShadowRootException, StaleElementReferenceException:
                if attempt == SHADOW_ROOT_RETRIES - 1:
                    raise
                self.logger.debug("Flow stage went stale, retrying", stage=stage, attempt=attempt)
                sleep(1)
        return None


class AppRedirectMixin:
    """Assert the browser lands back at an application after logging in"""

    def wait_for_app(self, destination: str):
        """Wait until the browser has landed back at the expected application URL"""
        try:
            self.wait.until(lambda driver: driver.current_url.startswith(destination))
        except TimeoutException:
            self.fail(
                "Expected to be redirected back to the application at "
                f"{destination} after logging in via the source, "
                f"but ended up at {self.driver.current_url}"
            )


class DexOAuthSourceMixin(FlowStageMixin):
    """Run a dex IdP container and create a matching OAuth source"""

    def setUp(self):
        self.client_secret = generate_id()
        self.slug = generate_id()
        super().setUp()
        self.run_container(
            image="ghcr.io/dexidp/dex:v2.44.0",
            ports={"5556": "5556"},
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:5556/dex/healthz"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            environment={
                "AK_HOST": self.host,
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

    def create_source(self, **kwargs) -> OAuthSource:
        """Create an OAuth source pointing at dex, and show it on the login page"""
        kwargs.setdefault(
            "authentication_flow", Flow.objects.get(slug="default-source-authentication")
        )
        kwargs.setdefault("enrollment_flow", Flow.objects.get(slug="default-source-enrollment"))
        source = OAuthSource.objects.create(  # nosec
            name=generate_id(),
            slug=self.slug,
            provider_type="openidconnect",
            authorization_url=f"http://{self.host}:5556/dex/auth",
            access_token_url=f"http://{self.host}:5556/dex/token",
            profile_url=f"http://{self.host}:5556/dex/userinfo",
            consumer_key="example-app",
            consumer_secret=self.client_secret,
            **kwargs,
        )
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([source])
        ident_stage.save()
        return source

    def login_via_oauth_provider(self):
        """Perform login at the OAuth provider (Dex)"""
        self.wait.until(ec.presence_of_element_located((By.ID, "login")))

        initial_provider_url = self.driver.current_url

        self.driver.find_element(By.ID, "login").send_keys("admin@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]")))

        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        self.wait.until(ec.url_changes(initial_provider_url))

        self.assertNotEqual(
            initial_provider_url,
            self.driver.current_url,
            "Expected to be redirected after login at OAuth provider",
        )

    @retry(is_test_case=False)
    def click_source_button(self):
        """Click the source button on the identification stage"""
        selector = "fieldset[name='login-sources'] button"
        identification_stage = self.get_stage_shadow_root("ak-stage-identification")

        WebDriverWait(identification_stage, self.wait_timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        identification_stage.find_element(By.CSS_SELECTOR, selector).click()

    def enroll_username(self, username: str):
        """Fill in the username asked for by the source enrollment prompt"""
        prompt_stage = self.get_stage_shadow_root("ak-stage-prompt")

        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").click()
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys(username)
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys(Keys.ENTER)


class SourceAppRedirectMixin(AppRedirectMixin, DexOAuthSourceMixin):
    """Log in at an application via an OAuth source, and assert we land back at the app.

    Subclasses provide the application (`setup_app`), its claim assertions
    (`assert_app_login`) and the URLs it is expected to be reached at; the tests
    below are identical for every provider type.
    """

    def setup_app(self) -> None:
        """Create the provider + application, and start the container acting as the app"""
        raise NotImplementedError

    def assert_app_login(self, user: User, entry_uri: str) -> None:
        """Assert the app logged `user` in, having been entered at `entry_uri`"""
        raise NotImplementedError

    def app_destination_url(self) -> str:
        """The URL the application is expected to be reached at once login is done"""
        raise NotImplementedError

    def deep_link_destination_url(self) -> str:
        """Where a login started at `DEEP_LINK_URL` is expected to land"""
        raise NotImplementedError

    def pass_consent(self):
        """Click through the consent stage, for applications that trigger one"""

    def restart_at_app(self, entry: str):
        """Start a fresh login at the app, discarding any session it kept for itself.

        Cookies are scoped to the current domain, so this only clears the app's own
        session (the app and authentik are served from different hosts).
        """
        self.driver.get(entry)
        self.driver.delete_all_cookies()
        self.driver.get(entry)

    def source_auth(self, entry: str, destination: str):
        """Log in at `entry` via the source as a user that already exists"""
        user = create_test_user(email="admin@example.com")
        self.create_source(user_matching_mode=SourceUserMatchingModes.EMAIL_LINK)
        self.setup_app()

        self.driver.get(entry)
        self.click_source_button()
        self.login_via_oauth_provider()

        self.pass_consent()
        self.wait_for_app(destination)
        self.assert_app_login(user, initial_uri(entry))

    def source_enroll(self, entry: str, destination: str):
        """Log in at `entry` via the source, enrolling a new user on the way"""
        self.create_source()
        self.setup_app()

        self.driver.get(entry)
        self.click_source_button()
        self.login_via_oauth_provider()

        # At this point we've been redirected back and we're asked for the username
        self.enroll_username("foo")

        self.pass_consent()
        self.wait_for_app(destination)
        # `name` comes from dex's static user, `username` from the enrollment prompt
        self.assert_app_login(
            User(username="foo", name="admin", email="admin@example.com"), initial_uri(entry)
        )

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
    @apply_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
    @apply_blueprint("system/providers-oauth2.yaml", "system/providers-saml.yaml")
    @reconcile_app("authentik_crypto")
    def test_source_auth(self):
        """test app login via OAuth source (existing user, linked by email)"""
        self.source_auth(APP_URL, self.app_destination_url())

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
    @apply_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
    @apply_blueprint("system/providers-oauth2.yaml", "system/providers-saml.yaml")
    @reconcile_app("authentik_crypto")
    def test_source_enroll(self):
        """test app login via OAuth source (new user, enrolled)"""
        self.source_enroll(APP_URL, self.app_destination_url())

    @retry()
    def test_source_enroll_auth(self):
        """test app login via OAuth source (enroll, then authenticate again)"""
        self.test_source_enroll()

        # We're logged in at the end of this, log out and re-login via the source.
        # The app is already running, so don't call setup_app() again.
        self.driver.get(self.url("authentik_flows:default-invalidation"))
        sleep(1)

        self.restart_at_app(APP_URL)
        self.click_source_button()
        self.login_via_oauth_provider()

        self.pass_consent()
        self.wait_for_app(self.app_destination_url())
        # `name` comes from dex's static user, `username` from the enrollment prompt
        self.assert_app_login(
            User(username="foo", name="admin", email="admin@example.com"), initial_uri(APP_URL)
        )

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
    @apply_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
    @apply_blueprint("system/providers-oauth2.yaml", "system/providers-saml.yaml")
    @reconcile_app("authentik_crypto")
    def test_source_auth_deep_link(self):
        """test app login via OAuth source, started at a deep link into the app"""
        self.source_auth(DEEP_LINK_URL, self.deep_link_destination_url())

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
    @apply_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
    @apply_blueprint("system/providers-oauth2.yaml", "system/providers-saml.yaml")
    @reconcile_app("authentik_crypto")
    def test_source_enroll_deep_link(self):
        """test app enrollment via OAuth source, started at a deep link into the app"""
        self.source_enroll(DEEP_LINK_URL, self.deep_link_destination_url())
