"""test flow with WebAuthn Stage"""

from time import sleep
from urllib.parse import parse_qs, urlsplit

from selenium.webdriver.common.by import By
from selenium.webdriver.common.virtual_authenticator import (
    Protocol,
    Transport,
    VirtualAuthenticatorOptions,
)
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import SCOPE_OPENID
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_brand
from authentik.flows.models import Flow, FlowAuthenticationRequirement
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from authentik.stages.authenticator_webauthn.models import (
    AuthenticatorWebAuthnStage,
    WebAuthnDevice,
)
from authentik.stages.identification.models import IdentificationStage
from tests.decorators import retry
from tests.e2e.test_flows_login_sfe import login_sfe
from tests.selenium import SeleniumTestCase


class TestFlowsAuthenticatorWebAuthn(SeleniumTestCase):
    """test flow with WebAuthn Stage"""

    host = "localhost"

    def add_virtual_authenticator(self):
        """Attach a new virtual authenticator. Each one has its own credential store, so
        attaching a second one models plugging in a second, distinct security key."""
        options = VirtualAuthenticatorOptions(
            protocol=Protocol.CTAP2,
            transport=Transport.INTERNAL,
            has_resident_key=True,
            has_user_verification=True,
            is_user_verified=True,
        )
        self.driver.add_virtual_authenticator(options)

    def start_enrollment(self):
        """Navigate to the WebAuthn setup stage's configuration flow"""
        self.driver.get(
            self.url(
                "authentik_flows:configure",
                stage_uuid=AuthenticatorWebAuthnStage.objects.first().stage_uuid,
            )
        )

    def register(self):
        self.add_virtual_authenticator()

        self.driver.get(self.url("authentik_core:if-flow", flow_slug="default-authentication-flow"))
        self.login()

        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)

        self.start_enrollment()

        self.wait_for_url(self.if_user_url("/library"))
        self.assertTrue(WebAuthnDevice.objects.filter(user=self.user, confirmed=True).exists())

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint("default/flow-default-authenticator-webauthn-setup.yaml")
    def test_webauthn_setup(self):
        """Test WebAuthn setup"""
        self.register()

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint("default/flow-default-authenticator-webauthn-setup.yaml")
    def test_webauthn_setup_duplicate_denied(self):
        """Test that the same authenticator can't be enrolled twice.

        The already-registered credential is sent in excludeCredentials, so the authenticator
        itself refuses to create a second credential and the browser raises InvalidStateError."""
        self.register()

        self.start_enrollment()

        flow_executor = self.get_shadow_root("ak-flow-executor")
        stage = self.get_shadow_root("ak-stage-authenticator-webauthn", flow_executor)
        WebDriverWait(stage, 10).until(
            lambda s: "already registered" in s.find_element(By.CSS_SELECTOR, "ak-empty-state").text
        )
        self.assertEqual(WebAuthnDevice.objects.filter(user=self.user).count(), 1)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint("default/flow-default-authenticator-webauthn-setup.yaml")
    def test_webauthn_setup_second_authenticator(self):
        """Test that a second, distinct authenticator can be enrolled on the same account.

        This is the case that the removed `prevent_duplicate_devices` option broke, as two
        security keys from the same batch share an attestation certificate."""
        self.register()

        # Swap in a different virtual authenticator, i.e. a second physical key
        self.driver.remove_virtual_authenticator()
        self.add_virtual_authenticator()

        self.start_enrollment()

        self.wait_for_url(self.if_user_url("/library"))
        self.assertEqual(WebAuthnDevice.objects.filter(user=self.user).count(), 2)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint("default/flow-default-authenticator-webauthn-setup.yaml")
    def test_webauthn_authenticate(self):
        """Test WebAuthn authentication"""
        self.register()
        self.driver.delete_all_cookies()

        self.driver.get(self.url("authentik_core:if-flow", flow_slug="default-authentication-flow"))
        self.login()

        self.wait_for_url(self.if_user_url("/library"))

        self.assert_user(self.user)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
        "default/flow-default-authenticator-webauthn-setup.yaml",
        "default/flow-default-provider-authorization-implicit-consent.yaml",
        "system/providers-oauth2.yaml",
    )
    def test_oidc_prompt_login_with_webauthn(self):
        """A logged-out prompt=login request returns a code after one MFA login."""
        auth_flow = Flow.objects.get(slug="default-authentication-flow")
        auth_flow.authentication = FlowAuthenticationRequirement.REQUIRE_UNAUTHENTICATED
        auth_flow.save()
        create_test_brand(flow_authentication=auth_flow)

        callback_url = self.url("authentik_api:user-me")
        app_name = generate_id()
        provider = OAuth2Provider.objects.create(
            name=app_name,
            client_id=generate_id(),
            client_type=ClientType.PUBLIC,
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, callback_url)],
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        provider.property_mappings.add(ScopeMapping.objects.get(scope_name=SCOPE_OPENID))
        Application.objects.create(name=app_name, slug=app_name, provider=provider)

        self.register()
        device = WebAuthnDevice.objects.get(user=self.user, confirmed=True)
        previous_use = device.last_used
        self.driver.delete_all_cookies()

        state = generate_id()
        challenge = pkce_s256_challenge(generate_id(43))
        self.driver.get(
            self.url(
                "authentik_providers_oauth2:authorize",
                query={
                    "client_id": provider.client_id,
                    "response_type": "code",
                    "scope": SCOPE_OPENID,
                    "redirect_uri": callback_url,
                    "state": state,
                    "prompt": "login",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                },
            )
        )
        self.login()

        self.wait.until(
            lambda driver: driver.current_url.startswith(f"{callback_url}?"),
            "Expected the OIDC callback after a single login",
        )
        params = parse_qs(urlsplit(self.driver.current_url).query)
        self.assertNotIn("error", params)
        self.assertEqual(params.get("state"), [state])
        self.assertIn("code", params)
        code = AuthorizationCode.objects.get(
            code=params["code"][0], provider=provider, user=self.user
        )
        self.assertEqual(code.code_challenge, challenge)
        self.assertEqual(code.code_challenge_method, "S256")
        device.refresh_from_db()
        self.assertIsNotNone(device.last_used)
        self.assertNotEqual(device.last_used, previous_use)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint("default/flow-default-authenticator-webauthn-setup.yaml")
    def test_webauthn_authenticate_sfe(self):
        """Test WebAuthn authentication (SFE)"""
        self.register()
        self.driver.delete_all_cookies()

        self.driver.get(
            self.url(
                "authentik_core:if-flow",
                flow_slug="default-authentication-flow",
                query={"sfe": True},
            )
        )
        login_sfe(self.driver, self.user)
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint("default/flow-default-authenticator-webauthn-setup.yaml")
    def test_passkey_login(self):
        """Test passkey login at identification stage"""
        self.register()

        # Configure identification stage to allow passkey login
        webauthn_validate_stage = AuthenticatorValidateStage.objects.get(
            name="default-authentication-mfa-validation"
        )
        ident_stage = IdentificationStage.objects.get(name="default-authentication-identification")
        ident_stage.webauthn_stage = webauthn_validate_stage
        ident_stage.save()

        self.driver.delete_all_cookies()

        # Navigate to login page
        self.driver.get(self.url("authentik_core:if-flow", flow_slug="default-authentication-flow"))

        # Wait for identification stage to load (ensures passkey challenge is triggered)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        self.get_shadow_root("ak-stage-identification", flow_executor)

        # The virtual authenticator should automatically respond to the conditional WebAuthn request
        # triggered by the identification stage when passkey_challenge is present.
        # We need to wait for the passkey autofill to trigger and complete.
        sleep(2)

        # If passkey auth succeeded, we should skip password and MFA stages
        # and go directly to the library
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)
