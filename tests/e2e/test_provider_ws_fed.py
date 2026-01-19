"""test WSFed Provider flow"""

from json import dumps

from selenium.webdriver.common.by import By

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLPropertyMapping
from tests.e2e.utils import SeleniumTestCase, retry


class TestProviderWSFed(SeleniumTestCase):
    """test WS Federation flow"""

    def setup_client(self, provider: WSFederationProvider, app: Application, **kwargs):
        metadata_url = (
            self.url(
                "authentik_api:wsfederationprovider-metadata",
                pk=provider.pk,
            )
            + "?download"
        )
        self.run_container(
            image="ghcr.io/beryju/wsfed-test-sp:v0.1.1",
            ports={
                "8080": "8080",
            },
            environment={
                "WSFED_TEST_SP_WTREALM": f"goauthentik.io://app/{app.slug}",
                "WSFED_TEST_SP_METADATA": metadata_url,
                **kwargs,
            },
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-saml.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_sp_initiated_implicit(self):
        """test WSFed Provider flow SP-initiated flow (implicit consent)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider = WSFederationProvider.objects.create(
            name=generate_id(),
            acs_url="http://localhost:8080/signin-wsfed",
            authorization_flow=authorization_flow,
            signing_kp=create_test_cert(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        provider.save()
        app = Application.objects.create(
            name="WSFed",
            slug=generate_id(),
            provider=provider,
        )
        self.setup_client(provider, app)
        self.driver.get("http://localhost:8080")
        self.login()
        self.wait_for_url("http://localhost:8080/")

        body = self.parse_json_content(self.driver.find_element(By.CSS_SELECTOR, "pre"))
        snippet = dumps(body, indent=2)[:500].replace("\n", " ")

        self.assertEqual(
            body.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"),
            self.user.name,
            f"Claim 'name' mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            body.get("http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"),
            self.user.username,
            f"Claim 'windowsaccountname' mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            body.get("http://schemas.goauthentik.io/2021/02/saml/username"),
            self.user.username,
            f"Claim 'saml/username' mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            body.get("http://schemas.goauthentik.io/2021/02/saml/uid"),
            str(self.user.pk),
            f"Claim 'saml/uid' mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            body.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"),
            self.user.email,
            f"Claim 'emailaddress' mismatch at {self.driver.current_url}: {snippet}",
        )

        self.assertEqual(
            body.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"),
            self.user.email,
            f"Claim 'upn' mismatch at {self.driver.current_url}: {snippet}",
        )
