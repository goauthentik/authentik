"""test SAML Provider flow"""
from json import loads
from sys import platform
from time import sleep
from unittest.case import skipUnless

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.saml.models import (
    SAMLBindings,
    SAMLPropertyMapping,
    SAMLProvider,
)
from tests.e2e.utils import USER, SeleniumTestCase, retry

LOGGER = get_logger()


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderSAML(SeleniumTestCase):
    """test SAML Provider flow"""

    container: Container

    def setup_client(self, provider: SAMLProvider) -> Container:
        """Setup client saml-sp container which we test SAML against"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="docker.beryju.org/proxy/beryju/saml-test-sp",
            detach=True,
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:9009/health"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            environment={
                "SP_ENTITY_ID": provider.issuer,
                "SP_SSO_BINDING": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "SP_METADATA_URL": (
                    self.url(
                        "authentik_providers_saml:metadata",
                        application_slug=provider.application.slug,
                    )
                ),
            },
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            LOGGER.info("Container failed healthcheck")
            sleep(1)

    @retry()
    def test_sp_initiated_implicit(self):
        """test SAML Provider flow SP-initiated flow (implicit consent)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider: SAMLProvider = SAMLProvider.objects.create(
            name="saml-test",
            acs_url="http://localhost:9009/saml/acs",
            audience="authentik-e2e",
            issuer="authentik-e2e",
            sp_binding=SAMLBindings.POST,
            authorization_flow=authorization_flow,
            signing_kp=CertificateKeyPair.objects.first(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        provider.save()
        Application.objects.create(
            name="SAML",
            slug="authentik-saml",
            provider=provider,
        )
        self.container = self.setup_client(provider)
        self.driver.get("http://localhost:9009")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["attr"]["cn"], [USER().name])
        self.assertEqual(body["attr"]["displayName"], [USER().username])
        self.assertEqual(body["attr"]["eduPersonPrincipalName"], [USER().email])
        self.assertEqual(body["attr"]["mail"], [USER().email])
        self.assertEqual(body["attr"]["uid"], [str(USER().pk)])

    @retry()
    def test_sp_initiated_explicit(self):
        """test SAML Provider flow SP-initiated flow (explicit consent)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-explicit-consent"
        )
        provider: SAMLProvider = SAMLProvider.objects.create(
            name="saml-test",
            acs_url="http://localhost:9009/saml/acs",
            audience="authentik-e2e",
            issuer="authentik-e2e",
            sp_binding=SAMLBindings.POST,
            authorization_flow=authorization_flow,
            signing_kp=CertificateKeyPair.objects.first(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        provider.save()
        app = Application.objects.create(
            name="SAML",
            slug="authentik-saml",
            provider=provider,
        )
        self.container = self.setup_client(provider)
        self.driver.get("http://localhost:9009")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.assertEqual(
            app.name,
            self.driver.find_element(By.ID, "application-name").text,
        )
        sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["attr"]["cn"], [USER().name])
        self.assertEqual(body["attr"]["displayName"], [USER().username])
        self.assertEqual(body["attr"]["eduPersonPrincipalName"], [USER().email])
        self.assertEqual(body["attr"]["mail"], [USER().email])
        self.assertEqual(body["attr"]["uid"], [str(USER().pk)])

    @retry()
    def test_idp_initiated_implicit(self):
        """test SAML Provider flow IdP-initiated flow (implicit consent)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider: SAMLProvider = SAMLProvider.objects.create(
            name="saml-test",
            acs_url="http://localhost:9009/saml/acs",
            audience="authentik-e2e",
            issuer="authentik-e2e",
            sp_binding=SAMLBindings.POST,
            authorization_flow=authorization_flow,
            signing_kp=CertificateKeyPair.objects.first(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        provider.save()
        Application.objects.create(
            name="SAML",
            slug="authentik-saml",
            provider=provider,
        )
        self.container = self.setup_client(provider)
        self.driver.get(
            self.url(
                "authentik_providers_saml:sso-init",
                application_slug=provider.application.slug,
            )
        )
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        sleep(1)
        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["attr"]["cn"], [USER().name])
        self.assertEqual(body["attr"]["displayName"], [USER().username])
        self.assertEqual(body["attr"]["eduPersonPrincipalName"], [USER().email])
        self.assertEqual(body["attr"]["mail"], [USER().email])
        self.assertEqual(body["attr"]["uid"], [str(USER().pk)])

    @retry()
    def test_sp_initiated_denied(self):
        """test SAML Provider flow SP-initiated flow (Policy denies access)"""
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        negative_policy = ExpressionPolicy.objects.create(
            name="negative-static", expression="return False"
        )
        provider: SAMLProvider = SAMLProvider.objects.create(
            name="saml-test",
            acs_url="http://localhost:9009/saml/acs",
            audience="authentik-e2e",
            issuer="authentik-e2e",
            sp_binding=SAMLBindings.POST,
            authorization_flow=authorization_flow,
            signing_kp=CertificateKeyPair.objects.first(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        provider.save()
        app = Application.objects.create(
            name="SAML",
            slug="authentik-saml",
            provider=provider,
        )
        PolicyBinding.objects.create(target=app, policy=negative_policy, order=0)
        self.container = self.setup_client(provider)
        self.driver.get("http://localhost:9009/")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "header > h1"))
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "header > h1").text,
            "Permission denied",
        )
