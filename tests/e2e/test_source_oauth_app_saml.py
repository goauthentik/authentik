"""test OAuth Source login into a SAML application"""

from json import dumps

from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_cert
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from tests.e2e.oauth_source import (
    APP_URL,
    AUTHORIZATION_FLOW,
    DEEP_LINK_URL,
    SourceAppRedirectMixin,
)
from tests.selenium import SeleniumTestCase

CLAIM = "http://schemas.goauthentik.io/2021/02/saml/username"
CLAIM_EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"


class TestSourceOAuthAppSAML(SourceAppRedirectMixin, SeleniumTestCase):
    """test OAuth Source login into a SAML application"""

    def setup_app(self):
        provider: SAMLProvider = SAMLProvider.objects.create(
            name=generate_id(),
            acs_url=f"{APP_URL}/saml/acs",
            audience="authentik-e2e",
            issuer_override="authentik-e2e",
            sp_binding=SAMLBindings.POST,
            authorization_flow=Flow.objects.get(slug=AUTHORIZATION_FLOW),
            signing_kp=create_test_cert(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        Application.objects.create(name="SAML", slug=generate_id(), provider=provider)
        self.run_container(
            image=self.pinned_image("saml-test-sp", "e2e/compose.yml"),
            ports={"9009": "9009"},
            environment={
                "SP_ENTITY_ID": provider.issuer_override,
                "SP_SSO_BINDING": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "SP_METADATA_URL": self.url("authentik_api:samlprovider-metadata", pk=provider.pk)
                + "?download",
            },
        )

    def pass_consent(self):
        """The SP doesn't ask for consent"""

    def app_destination_url(self):
        return f"{APP_URL}/"

    def deep_link_destination_url(self):
        # The SP carries the originally requested path through the login via RelayState
        return DEEP_LINK_URL

    def assert_app_login(self, user: User, entry_uri: str):
        body = self.parse_json_content()
        snippet = dumps(body, indent=2)[:500].replace("\n", " ")
        attrs = body.get("attr", {})

        for claim, expected in ((CLAIM, user.username), (CLAIM_EMAIL, user.email)):
            self.assertEqual(
                attrs.get(claim),
                [expected],
                f"Claim {claim} mismatch at {self.driver.current_url}: {snippet}",
            )
