"""test flow with WebAuthn Stage"""

from selenium.webdriver.common.virtual_authenticator import (
    Protocol,
    Transport,
    VirtualAuthenticatorOptions,
)

from authentik.blueprints.tests import apply_blueprint
from authentik.stages.authenticator_webauthn.models import (
    AuthenticatorWebAuthnStage,
    WebAuthnDevice,
)
from tests.e2e.test_flows_login_sfe import login_sfe
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsAuthenticatorWebAuthn(SeleniumTestCase):
    """test flow with WebAuthn Stage"""

    host = "localhost"

    def register(self):
        options = VirtualAuthenticatorOptions(
            protocol=Protocol.CTAP2,
            transport=Transport.INTERNAL,
            has_resident_key=True,
            has_user_verification=True,
            is_user_verified=True,
        )
        self.driver.add_virtual_authenticator(options)

        self.driver.get(self.url("authentik_core:if-flow", flow_slug="default-authentication-flow"))
        self.login()

        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)

        self.driver.get(
            self.url(
                "authentik_flows:configure",
                stage_uuid=AuthenticatorWebAuthnStage.objects.first().stage_uuid,
            )
        )

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
