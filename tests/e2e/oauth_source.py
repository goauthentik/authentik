"""Helpers for tests that log into an application via a source"""

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
from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_cert
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
REDIRECT_URI = f"{APP_URL}/auth/callback"
AUTHORIZATION_FLOW = "default-provider-authorization-implicit-consent"
# dex's static user
DEX_USER = "admin"
DEX_EMAIL = "admin@example.com"
DEX_PASSWORD = "password"  # nosec


def source_app_test(func):
    """Apply the blueprints and retries these tests share"""
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


@retry(is_test_case=False)
def stage_shadow_root(test, stage: str):
    """Get a flow stage's shadow root, retrying while the executor swaps stages"""
    for attempt in range(SHADOW_ROOT_RETRIES):
        try:
            return test.get_shadow_root(stage, test.get_shadow_root("ak-flow-executor"))
        except DetachedShadowRootException, StaleElementReferenceException:
            if attempt == SHADOW_ROOT_RETRIES - 1:
                raise
            sleep(1)
    return None


def click_source_button(test):
    """Click the source button on the identification stage"""
    selector = "fieldset[name='login-sources'] button"
    identification_stage = stage_shadow_root(test, "ak-stage-identification")
    WebDriverWait(identification_stage, test.wait_timeout).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    identification_stage.find_element(By.CSS_SELECTOR, selector).click()


def fill_prompt(test, field: str, value: str):
    """Fill in a single field of a prompt stage"""
    element = stage_shadow_root(test, "ak-stage-prompt").find_element(
        By.CSS_SELECTOR, f"input[name={field}]"
    )
    element.click()
    element.send_keys(value)
    element.send_keys(Keys.ENTER)


def wait_for_app(test, destination: str):
    """Wait until the browser has landed back at the application"""
    try:
        test.wait.until(lambda driver: driver.current_url.startswith(destination))
    except TimeoutException:
        test.fail(
            f"Expected to be redirected back to the application at {destination} "
            f"after logging in via the source, but ended up at {test.driver.current_url}"
        )


class TestOAuthSource:
    """An OAuth source, backed by a dex container"""

    __test__ = False

    def __init__(self, test):
        self.test = test
        self.slug = generate_id()
        self.client_secret = generate_id()

    def start(self):
        """Run the dex container"""
        self.test.run_container(
            image=self.test.pinned_image("dex", "e2e/compose.yml"),
            ports={"5556": "5556"},
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:5556/dex/healthz"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            environment={
                "AK_HOST": self.test.host,
                "AK_REDIRECT_URL": self.test.url(
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

    def create(self, show_on_login=True, **kwargs) -> OAuthSource:
        """Create the source, and show it on the login page"""
        host = self.test.host
        kwargs.setdefault(
            "authentication_flow", Flow.objects.get(slug="default-source-authentication")
        )
        kwargs.setdefault("enrollment_flow", Flow.objects.get(slug="default-source-enrollment"))
        self.source = OAuthSource.objects.create(  # nosec
            name=generate_id(),
            slug=self.slug,
            provider_type="openidconnect",
            authorization_url=f"http://{host}:5556/dex/auth",
            access_token_url=f"http://{host}:5556/dex/token",
            profile_url=f"http://{host}:5556/dex/userinfo",
            consumer_key="example-app",
            consumer_secret=self.client_secret,
            **kwargs,
        )
        if show_on_login:
            ident_stage = IdentificationStage.objects.first()
            ident_stage.sources.set([self.source])
            ident_stage.save()
        return self.source

    def login(self):
        """Log in at dex"""
        self.test.wait.until(ec.presence_of_element_located((By.ID, "login")))
        current_url = self.test.driver.current_url

        self.test.driver.find_element(By.ID, "login").send_keys(DEX_EMAIL)
        self.test.driver.find_element(By.ID, "password").send_keys(DEX_PASSWORD)
        self.test.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        self.test.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "button[type=submit]"))
        )
        self.test.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        self.test.wait.until(ec.url_changes(current_url))

    def auth(self):
        """Pick this source on the login page and authenticate as an existing user"""
        click_source_button(self.test)
        self.login()

    def enroll(self, username="foo") -> User:
        """Pick this source on the login page and enroll a new user"""
        self.auth()
        fill_prompt(self.test, "username", username)
        # `name` comes from dex, `username` from the enrollment prompt
        return User(username=username, name=DEX_USER, email=DEX_EMAIL)


class TestOIDCApp:
    """An OIDC application, backed by an oidc-test-client container"""

    __test__ = False

    scopes = [SCOPE_OPENID, SCOPE_OFFLINE_ACCESS, SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL]

    def __init__(self, test, scopes: list[str] | None = None):
        self.test = test
        self.slug = generate_id()
        self.client_id = generate_id()
        self.client_secret = generate_key()
        self.scopes = scopes or self.scopes

    def start(self, *extra_mappings: ScopeMapping):
        """Create the provider and application, and run the client container"""
        provider = OAuth2Provider.objects.create(
            name=self.slug,
            client_type=ClientType.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            signing_key=create_test_cert(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            authorization_flow=Flow.objects.get(slug=AUTHORIZATION_FLOW),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
        )
        provider.property_mappings.set(
            [*ScopeMapping.objects.filter(scope_name__in=self.scopes), *extra_mappings]
        )
        Application.objects.create(name=self.slug, slug=self.slug, provider=provider)
        # The application has to exist before the client fetches the discovery document
        self.test.run_container(
            image=self.test.pinned_image("oidc-test-client", "e2e/compose.yml"),
            ports={"9009": "9009"},
            environment={
                "OIDC_CLIENT_ID": self.client_id,
                "OIDC_CLIENT_SECRET": self.client_secret,
                "OIDC_PROVIDER": f"{self.test.live_server_url}/application/o/{self.slug}/",
                "OIDC_SCOPES": ",".join(self.scopes),
            },
        )

    def open(self, url=APP_URL):
        """Browse to the application, which starts the authorization"""
        self.test.driver.get(url)

    def reopen(self, url=APP_URL):
        """Browse to the application again, discarding the session it kept for itself"""
        self.test.driver.get(url)
        self.test.driver.delete_all_cookies()
        self.test.driver.get(url)

    def consent(self):
        """Click through the consent stage the client asks for"""
        try:
            self.test.wait.until(ec.url_contains(f"/if/flow/{AUTHORIZATION_FLOW}/"))
        except TimeoutException:
            self.test.fail(
                "Expected the application's authorization to resume, but ended up at "
                f"{self.test.driver.current_url}"
            )
        stage_shadow_root(self.test, "ak-stage-consent").find_element(
            By.CSS_SELECTOR, "[type=submit]"
        ).click()

    def assert_login(self, user: User, entry=APP_URL, **claims):
        """Assert the application logged `user` in, having been entered at `entry`"""
        self.consent()
        # The client always lands on its redirect URI, and reports where it started
        # as InitialURL
        wait_for_app(self.test, REDIRECT_URI)
        body = self.test.parse_json_content()
        token = body.get("IDTokenClaims", {})
        expected = {
            "nickname": user.username,
            "email": user.email,
            **claims,
        }
        for claim, want in expected.items():
            self.test.assertEqual(
                token.get(claim), want, f"{claim} mismatch at {self.test.driver.current_url}"
            )
        parts = urlsplit(entry)
        self.test.assertEqual(
            body.get("InitialURL"),
            urlunsplit(("", "", parts.path or "/", parts.query, "")) or "/",
            f"InitialURL mismatch at {self.test.driver.current_url}",
        )
