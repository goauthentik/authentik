"""Shared tooling for SAML source e2e tests"""

from pathlib import Path

from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from tests.e2e.test_source_saml import IDP_CERT, IDP_KEY

# The static user shipped by the test IdP image, and the email it asserts. With
# SIMPLESAMLPHP_SP_NAME_ID_ATTRIBUTE=email the NameID *is* this address, which is
# also the identifier a UserSAMLSourceConnection is keyed on.
IDP_USERNAME = "user1"
IDP_PASSWORD = "user1pass"  # nosec
IDP_EMAIL = "user1@example.com"


class SAMLIdPMixin:
    """Run a SAML IdP container and create a matching SAML source"""

    def setUp(self):
        self.saml_slug = generate_id()
        super().setUp()
        self.run_container(
            image="kristophjunge/test-saml-idp:1.15",
            ports={"8080": "8080"},
            healthcheck=Healthcheck(
                test=["CMD", "curl", "http://localhost:8080"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
            volumes={
                str(
                    (Path(__file__).parent / Path("test-saml-idp/saml20-sp-remote.php")).absolute()
                ): {
                    "bind": "/var/www/simplesamlphp/metadata/saml20-sp-remote.php",
                    "mode": "ro",
                }
            },
            environment={
                "SIMPLESAMLPHP_SP_ENTITY_ID": "entity-id",
                "SIMPLESAMLPHP_SP_NAME_ID_FORMAT": (
                    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                ),
                "SIMPLESAMLPHP_SP_NAME_ID_ATTRIBUTE": "email",
                "SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE": (
                    self.url("authentik_sources_saml:acs", source_slug=self.saml_slug)
                ),
            },
        )

    def create_saml_source(self, **kwargs) -> SAMLSource:
        """Create a SAML source pointing at the test IdP"""
        kwargs.setdefault(
            "authentication_flow", Flow.objects.get(slug="default-source-authentication")
        )
        kwargs.setdefault("enrollment_flow", Flow.objects.get(slug="default-source-enrollment"))
        return SAMLSource.objects.create(
            name=generate_id(),
            slug=self.saml_slug,
            pre_authentication_flow=Flow.objects.get(slug="default-source-pre-authentication"),
            issuer_override="entity-id",
            sso_url=f"http://{self.host}:8080/simplesaml/saml2/idp/SSOService.php",
            binding_type=SAMLBindingTypes.REDIRECT,
            signing_kp=CertificateKeyPair.objects.create(
                name=generate_id(),
                certificate_data=IDP_CERT,
                key_data=IDP_KEY,
            ),
            **kwargs,
        )

    def login_via_saml_provider(self):
        """Perform login at the SAML IdP"""
        self.wait.until(ec.presence_of_element_located((By.ID, "username")))

        initial_provider_url = self.driver.current_url

        self.driver.find_element(By.ID, "username").send_keys(IDP_USERNAME)
        self.driver.find_element(By.ID, "password").send_keys(IDP_PASSWORD)
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        self.wait.until(ec.url_changes(initial_provider_url))
