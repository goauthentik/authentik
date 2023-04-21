"""test OAuth2 OpenID Provider flow"""
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
from authentik.lib.generators import generate_id, generate_key
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.constants import (
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.providers.oauth2.models import ClientTypes, OAuth2Provider, ScopeMapping
from tests.e2e.utils import SeleniumTestCase, retry


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
            image="ghcr.io/beryju/oidc-test-client:1.3",
            detach=True,
            network_mode="host",
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
            self.logger.info("Container failed healthcheck")
            sleep(1)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @reconcile_app("authentik_crypto")
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
            signing_key=create_test_cert(),
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
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @reconcile_app("authentik_crypto")
    @apply_blueprint("system/providers-oauth2.yaml")
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
            signing_key=create_test_cert(),
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
        self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, "pre"), "{"))
        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["IDTokenClaims"]["nickname"], self.user.username)
        self.assertEqual(body["UserInfo"]["nickname"], self.user.username)

        self.assertEqual(body["IDTokenClaims"]["name"], self.user.name)
        self.assertEqual(body["UserInfo"]["name"], self.user.name)

        self.assertEqual(body["IDTokenClaims"]["email"], self.user.email)
        self.assertEqual(body["UserInfo"]["email"], self.user.email)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @reconcile_app("authentik_crypto")
    @apply_blueprint("system/providers-oauth2.yaml")
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
            signing_key=create_test_cert(),
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
            "[type=submit]",
        ).click()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "pre")))
        self.wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, "pre"), "{"))
        body = loads(self.driver.find_element(By.CSS_SELECTOR, "pre").text)

        self.assertEqual(body["IDTokenClaims"]["nickname"], self.user.username)
        self.assertEqual(body["UserInfo"]["nickname"], self.user.username)

        self.assertEqual(body["IDTokenClaims"]["name"], self.user.name)
        self.assertEqual(body["UserInfo"]["name"], self.user.name)

        self.assertEqual(body["IDTokenClaims"]["email"], self.user.email)
        self.assertEqual(body["UserInfo"]["email"], self.user.email)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @reconcile_app("authentik_crypto")
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
            signing_key=create_test_cert(),
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
