"""test OAuth Source login into an OAuth2/OIDC application"""

from json import dumps

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

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
from tests.e2e.oauth_source import SourceAppRedirectMixin
from tests.selenium import SeleniumTestCase

AUTHORIZATION_FLOW = "default-provider-authorization-implicit-consent"
REDIRECT_URI = "http://localhost:9009/auth/callback"


class TestSourceOAuthAppOIDC(SourceAppRedirectMixin, SeleniumTestCase):
    """test OAuth Source login into an OAuth2/OIDC application"""

    def setUp(self):
        self.client_id = generate_id()
        self.app_client_secret = generate_key()
        self.application_slug = generate_id()
        super().setUp()

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
            ScopeMapping.objects.filter(
                scope_name__in=[
                    SCOPE_OPENID,
                    SCOPE_OPENID_EMAIL,
                    SCOPE_OPENID_PROFILE,
                    SCOPE_OFFLINE_ACCESS,
                ]
            )
        )
        Application.objects.create(
            name=self.application_slug,
            slug=self.application_slug,
            provider=provider,
        )
        # The application has to exist before the client fetches the discovery document
        self.run_container(
            image="ghcr.io/beryju/oidc-test-client:2.7.1",
            ports={"9009": "9009"},
            environment={
                "OIDC_CLIENT_ID": self.client_id,
                "OIDC_CLIENT_SECRET": self.app_client_secret,
                "OIDC_PROVIDER": f"{self.live_server_url}/application/o/{self.application_slug}/",
            },
        )

    def app_destination_url(self):
        return REDIRECT_URI

    def deep_link_destination_url(self):
        # The client always lands on its redirect URI; the URL the login started at
        # comes back in the token payload as InitialURL instead
        return REDIRECT_URI

    def pass_consent(self):
        # The test client requests offline_access and sends prompt=consent,
        # so a consent stage is shown even with an implicit-consent flow
        self.wait.until(ec.url_contains(f"/if/flow/{AUTHORIZATION_FLOW}/"))

        consent_stage = self.get_stage_shadow_root("ak-stage-consent")
        consent_stage.find_element(By.CSS_SELECTOR, "[type=submit]").click()

    def assert_app_login(self, user: User, entry_uri: str):
        body = self.parse_json_content()
        snippet = dumps(body, indent=2)[:500].replace("\n", " ")
        claims = body.get("IDTokenClaims", {})

        self.assertEqual(
            claims.get("nickname"),
            user.username,
            f"IDTokenClaims.nickname mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            claims.get("email"),
            user.email,
            f"IDTokenClaims.email mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            body.get("InitialURL"),
            entry_uri,
            f"InitialURL mismatch at {self.driver.current_url}: {snippet}",
        )
