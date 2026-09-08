"""Shared tooling for source-into-application e2e tests"""

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
from authentik.common.oauth.constants import (
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.core.models import Application, SourceUserMatchingModes, User
from authentik.core.tests.utils import create_test_cert, create_test_user
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.identification.models import IdentificationStage
from tests.decorators import SHADOW_ROOT_RETRIES, retry

APP_URL = "http://localhost:9009"
# A non-root app URL, to check the original destination survives the source login
DEEP_LINK_URL = f"{APP_URL}/deep/link"
AUTHORIZATION_FLOW = "default-provider-authorization-implicit-consent"
REDIRECT_URI = f"{APP_URL}/auth/callback"


def source_app_test(func):
    """Blueprints and retry every source-into-application test needs"""
    for deco in (
        reconcile_app("authentik_crypto"),
        apply_blueprint("system/providers-oauth2.yaml", "system/providers-saml.yaml"),
        apply_blueprint(f"default/flow-{AUTHORIZATION_FLOW}.yaml"),
        apply_blueprint(
            "default/flow-default-source-authentication.yaml",
            "default/flow-default-source-enrollment.yaml",
            "default/flow-default-source-pre-authentication.yaml",
        ),
        apply_blueprint(
            "default/flow-default-authentication-flow.yaml",
            "default/flow-default-invalidation-flow.yaml",
        ),
        retry(),
    ):
        func = deco(func)
    return func


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
                return self.get_shadow_root(stage, self.get_shadow_root("ak-flow-executor"))
            except DetachedShadowRootException, StaleElementReferenceException:
                if attempt == SHADOW_ROOT_RETRIES - 1:
                    raise
                sleep(1)
        return None

    def fill_prompt(self, field: str, value: str):
        """Fill in a single field of a prompt stage"""
        element = self.get_stage_shadow_root("ak-stage-prompt").find_element(
            By.CSS_SELECTOR, f"input[name={field}]"
        )
        element.click()
        element.send_keys(value)
        element.send_keys(Keys.ENTER)


class OIDCAppMixin(FlowStageMixin):
    """An OIDC application, served by the oidc-test-client container"""

    # The client sends prompt=consent for offline_access, so a consent stage is shown
    # even with an implicit-consent authorization flow
    scopes = [SCOPE_OPENID, SCOPE_OFFLINE_ACCESS, SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL]

    def setUp(self):
        self.client_id = generate_id()
        self.app_client_secret = generate_key()
        self.application_slug = generate_id()
        super().setUp()

    def extra_scope_mappings(self) -> list[ScopeMapping]:
        """Scope mappings on top of the defaults"""
        return []

    def setup_app(self):
        provider = OAuth2Provider.objects.create(
            name=self.application_slug,
            client_type=ClientType.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.app_client_secret,
            signing_key=create_test_cert(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            authorization_flow=Flow.objects.get(slug=AUTHORIZATION_FLOW),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
        )
        provider.property_mappings.set(
            [
                *ScopeMapping.objects.filter(scope_name__in=self.scopes),
                *self.extra_scope_mappings(),
            ]
        )
        Application.objects.create(
            name=self.application_slug, slug=self.application_slug, provider=provider
        )
        # The application has to exist before the client fetches the discovery document
        self.run_container(
            image=self.pinned_image("oidc-test-client", "e2e/compose.yml"),
            ports={"9009": "9009"},
            environment={
                "OIDC_CLIENT_ID": self.client_id,
                "OIDC_CLIENT_SECRET": self.app_client_secret,
                "OIDC_PROVIDER": f"{self.live_server_url}/application/o/{self.application_slug}/",
                "OIDC_SCOPES": ",".join(self.scopes),
            },
        )

    def pass_consent(self):
        """Click through the consent stage the client asks for"""
        try:
            self.wait.until(ec.url_contains(f"/if/flow/{AUTHORIZATION_FLOW}/"))
        except TimeoutException:
            self.fail(
                "Expected the pending application authorization to resume, but ended up at "
                f"{self.driver.current_url}"
            )
        self.get_stage_shadow_root("ak-stage-consent").find_element(
            By.CSS_SELECTOR, "[type=submit]"
        ).click()

    # The client always lands on its redirect URI; the URL the login started at comes
    # back in the token payload as InitialURL instead
    def app_destination_url(self) -> str:
        return REDIRECT_URI

    def deep_link_destination_url(self) -> str:
        return REDIRECT_URI


class AppRedirectMixin:
    """Assert the browser lands back at an application after logging in"""

    def wait_for_app(self, destination: str):
        try:
            self.wait.until(lambda driver: driver.current_url.startswith(destination))
        except TimeoutException:
            self.fail(
                f"Expected to be redirected back to the application at {destination} "
                f"after logging in via the source, but ended up at {self.driver.current_url}"
            )


class DexOAuthSourceMixin(FlowStageMixin):
    """Run a dex IdP container and create a matching OAuth source"""

    def setUp(self):
        self.client_secret = generate_id()
        self.slug = generate_id()
        super().setUp()
        self.run_container(
            image=self.pinned_image("dex", "e2e/compose.yml"),
            ports={"5556": "5556"},
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:5556/dex/healthz"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            environment={
                "AK_HOST": self.host,
                "AK_REDIRECT_URL": self.url(
                    "authentik_sources_oauth:oauth-client-callback", source_slug=self.slug
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

    @retry(is_test_case=False)
    def click_source_button(self):
        """Click the source button on the identification stage"""
        selector = "fieldset[name='login-sources'] button"
        identification_stage = self.get_stage_shadow_root("ak-stage-identification")

        WebDriverWait(identification_stage, self.wait_timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        identification_stage.find_element(By.CSS_SELECTOR, selector).click()


class SourceAppRedirectMixin(AppRedirectMixin, DexOAuthSourceMixin):
    """Log in at an application via an OAuth source, and assert we land back at the app.

    Subclasses provide the application (`setup_app`, `*_destination_url`, `pass_consent`)
    and its claim assertions (`assert_app_login`).
    """

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
        self.fill_prompt("username", "foo")

        self.pass_consent()
        self.wait_for_app(destination)
        self.assert_app_login(self.enrolled_user(), initial_uri(entry))

    def enrolled_user(self) -> User:
        """`name` comes from dex's static user, `username` from the enrollment prompt"""
        return User(username="foo", name="admin", email="admin@example.com")

    @source_app_test
    def test_source_auth(self):
        """test app login via OAuth source (existing user, linked by email)"""
        self.source_auth(APP_URL, self.app_destination_url())

    @source_app_test
    def test_source_enroll(self):
        """test app login via OAuth source (new user, enrolled)"""
        self.source_enroll(APP_URL, self.app_destination_url())

    @source_app_test
    def test_source_auth_deep_link(self):
        """test app login via OAuth source, started at a deep link into the app"""
        self.source_auth(DEEP_LINK_URL, self.deep_link_destination_url())

    @source_app_test
    def test_source_enroll_deep_link(self):
        """test app enrollment via OAuth source, started at a deep link into the app"""
        self.source_enroll(DEEP_LINK_URL, self.deep_link_destination_url())

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
        self.assert_app_login(self.enrolled_user(), initial_uri(APP_URL))
