"""test SAML Provider flow"""
from json import loads
from sys import platform
from time import sleep
from unittest.case import skipUnless

from docker import DockerClient, from_env
from docker.models.containers import Container
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert
from authentik.flows.models import Flow
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.sources.saml.processors.constants import SAML_BINDING_POST
from tests.e2e.utils import SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderSAML(SeleniumTestCase):
    """test SAML Provider flow"""

    container: Container

    def setup_client(self, provider: SAMLProvider, force_post: bool = False) -> Container:
        """Setup client saml-sp container which we test SAML against"""
        client: DockerClient = from_env()
        metadata_url = (
            self.url(
                "authentik_api:samlprovider-metadata",
                pk=provider.pk,
            )
            + "?download"
        )
        if force_post:
            metadata_url += f"&force_binding={SAML_BINDING_POST}"
        container = client.containers.run(
            image="ghcr.io/beryju/saml-test-sp:1.1",
            detach=True,
            network_mode="host",
            environment={
                "SP_ENTITY_ID": provider.issuer,
                "SP_SSO_BINDING": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "SP_METADATA_URL": metadata_url,
            },
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            self.logger.info("Container failed healthcheck")
            sleep(1)

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
            signing_kp=create_test_cert(),
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
        self.login()
        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"],
            [self.user.name],
        )
        self.assertEqual(
            body["attr"][
                "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"
            ],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/username"],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/uid"],
            [str(self.user.pk)],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"],
            [self.user.email],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"],
            [self.user.email],
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-saml.yaml",
    )
    @reconcile_app("authentik_crypto")
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
            signing_kp=create_test_cert(),
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
        self.login()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-flow-executor")))

        flow_executor = self.get_shadow_root("ak-flow-executor")
        consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)

        self.assertIn(
            app.name,
            consent_stage.find_element(By.CSS_SELECTOR, "#header-text").text,
        )
        consent_stage.find_element(
            By.CSS_SELECTOR,
            "[type=submit]",
        ).click()

        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"],
            [self.user.name],
        )
        self.assertEqual(
            body["attr"][
                "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"
            ],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/username"],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/uid"],
            [str(self.user.pk)],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"],
            [self.user.email],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"],
            [self.user.email],
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-saml.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_sp_initiated_explicit_post(self):
        """test SAML Provider flow SP-initiated flow (explicit consent) (POST binding)"""
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
            signing_kp=create_test_cert(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        provider.save()
        app = Application.objects.create(
            name="SAML",
            slug="authentik-saml",
            provider=provider,
        )
        self.container = self.setup_client(provider, True)
        self.driver.get("http://localhost:9009")
        self.login()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-flow-executor")))

        flow_executor = self.get_shadow_root("ak-flow-executor")
        consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)

        self.assertIn(
            app.name,
            consent_stage.find_element(By.CSS_SELECTOR, "#header-text").text,
        )
        consent_stage.find_element(
            By.CSS_SELECTOR,
            "[type=submit]",
        ).click()

        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"],
            [self.user.name],
        )
        self.assertEqual(
            body["attr"][
                "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"
            ],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/username"],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/uid"],
            [str(self.user.pk)],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"],
            [self.user.email],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"],
            [self.user.email],
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
            signing_kp=create_test_cert(),
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
        self.login()
        sleep(1)
        self.wait_for_url("http://localhost:9009/")

        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"],
            [self.user.name],
        )
        self.assertEqual(
            body["attr"][
                "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"
            ],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/username"],
            [self.user.username],
        )
        self.assertEqual(
            body["attr"]["http://schemas.goauthentik.io/2021/02/saml/uid"],
            [str(self.user.pk)],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"],
            [self.user.email],
        )
        self.assertEqual(
            body["attr"]["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"],
            [self.user.email],
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
            signing_kp=create_test_cert(),
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
        self.login()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "header > h1")))
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "header > h1").text,
            "Permission denied",
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
    def test_slo(self):
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
            signing_kp=create_test_cert(),
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
        self.login()
        self.wait_for_url("http://localhost:9009/")

        self.driver.get("http://localhost:9009/saml/logout")
        self.wait_for_url(
            self.url(
                "authentik_core:if-session-end",
                application_slug=app.slug,
            )
        )
