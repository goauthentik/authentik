"""test OAuth2 OpenID Provider flow"""
from json import loads
from sys import platform
from time import sleep
from unittest.case import skipUnless

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.constants import (
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.providers.oauth2.models import ClientTypes, OAuth2Provider, ScopeMapping
from tests.e2e.utils import USER, SeleniumTestCase, apply_migration, object_manager, retry

LOGGER = get_logger()


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderOAuth2OIDC(SeleniumTestCase):
    """test OAuth with OpenID Provider flow"""

    def setUp(self):
        self.client_id = generate_id()
        self.client_secret = generate_key()
        self.application_slug = "test"
        super().setUp()

    def setup_client(self) -> Container:
        """Setup client saml-sp container which we test SAML against"""
        sleep(1)
        client: DockerClient = from_env()
        container = client.containers.run(
            image="beryju.org/oidc-test-client:latest",
            detach=True,
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:9009/health"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            environment={
                "OIDC_CLIENT_ID": self.client_id,
                "OIDC_CLIENT_SECRET": self.client_secret,
                "OIDC_PROVIDER": f"{self.live_server_url}/application/o/{self.application_slug}/",
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
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0010_provider_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    def test_redirect_uri_error(self):
        """test OpenID Provider flow (invalid redirect URI, check error message)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name=self.application_slug,
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            rsa_key=CertificateKeyPair.objects.first(),
            redirect_uris="http://localhost:9009/",
            authorization_flow=authorization_flow,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        Application.objects.create(
            name=self.application_slug,
            slug=self.application_slug,
            provider=provider,
        )
        self.container = self.setup_client()

        self.driver.get("http://localhost:9009")
        sleep(2)
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "pf-c-title").text,
            "Redirect URI Error",
        )

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0010_provider_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    @object_manager
    def test_authorization_consent_implied(self):
        """test OpenID Provider flow (default authorization flow with implied consent)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name=self.application_slug,
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            rsa_key=CertificateKeyPair.objects.first(),
            redirect_uris="http://localhost:9009/auth/callback",
            authorization_flow=authorization_flow,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        Application.objects.create(
            name=self.application_slug,
            slug=self.application_slug,
            provider=provider,
        )
        self.container = self.setup_client()

        self.driver.get("http://localhost:9009")
        self.login()
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "pre")))
        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["IDTokenClaims"]["nickname"], USER().username)
        self.assertEqual(body["UserInfo"]["nickname"], USER().username)

        self.assertEqual(body["IDTokenClaims"]["name"], USER().name)
        self.assertEqual(body["UserInfo"]["name"], USER().name)

        self.assertEqual(body["IDTokenClaims"]["email"], USER().email)
        self.assertEqual(body["UserInfo"]["email"], USER().email)

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0010_provider_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    @object_manager
    def test_authorization_consent_explicit(self):
        """test OpenID Provider flow (default authorization flow with explicit consent)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-explicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name=self.application_slug,
            authorization_flow=authorization_flow,
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            rsa_key=CertificateKeyPair.objects.first(),
            redirect_uris="http://localhost:9009/auth/callback",
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        app = Application.objects.create(
            name=self.application_slug,
            slug=self.application_slug,
            provider=provider,
        )
        self.container = self.setup_client()

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
            ("[type=submit]"),
        ).click()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "pre")))
        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["IDTokenClaims"]["nickname"], USER().username)
        self.assertEqual(body["UserInfo"]["nickname"], USER().username)

        self.assertEqual(body["IDTokenClaims"]["name"], USER().name)
        self.assertEqual(body["UserInfo"]["name"], USER().name)

        self.assertEqual(body["IDTokenClaims"]["email"], USER().email)
        self.assertEqual(body["UserInfo"]["email"], USER().email)

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_flows", "0010_provider_flows")
    @apply_migration("authentik_crypto", "0002_create_self_signed_kp")
    def test_authorization_denied(self):
        """test OpenID Provider flow (default authorization with access deny)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-explicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name=self.application_slug,
            authorization_flow=authorization_flow,
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            rsa_key=CertificateKeyPair.objects.first(),
            redirect_uris="http://localhost:9009/auth/callback",
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        app = Application.objects.create(
            name=self.application_slug,
            slug=self.application_slug,
            provider=provider,
        )

        negative_policy = ExpressionPolicy.objects.create(
            name="negative-static", expression="return False"
        )
        PolicyBinding.objects.create(target=app, policy=negative_policy, order=0)

        self.container = self.setup_client()
        self.driver.get("http://localhost:9009")
        self.login()
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "header > h1")))
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "header > h1").text,
            "Permission denied",
        )
