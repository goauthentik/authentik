"""test OAuth2 OpenID Provider flow"""
from sys import platform
from time import sleep
from typing import Any, Optional
from unittest.case import skipUnless

from docker.types import Healthcheck
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
class TestProviderOAuth2OAuth(SeleniumTestCase):
    """test OAuth with OAuth Provider flow"""

    def setUp(self):
        self.client_id = generate_id()
        self.client_secret = generate_key()
        self.app_slug = generate_id(20)
        super().setUp()

    def get_container_specs(self) -> Optional[dict[str, Any]]:
        return {
            "image": "grafana/grafana:7.1.0",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
            "healthcheck": Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:3000"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
            "environment": {
                "GF_AUTH_GENERIC_OAUTH_ENABLED": "true",
                "GF_AUTH_GENERIC_OAUTH_CLIENT_ID": self.client_id,
                "GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET": self.client_secret,
                "GF_AUTH_GENERIC_OAUTH_SCOPES": "openid email profile",
                "GF_AUTH_GENERIC_OAUTH_AUTH_URL": self.url("authentik_providers_oauth2:authorize"),
                "GF_AUTH_GENERIC_OAUTH_TOKEN_URL": self.url("authentik_providers_oauth2:token"),
                "GF_AUTH_GENERIC_OAUTH_API_URL": self.url("authentik_providers_oauth2:userinfo"),
                "GF_AUTH_SIGNOUT_REDIRECT_URL": self.url(
                    "authentik_providers_oauth2:end-session",
                    application_slug=self.app_slug,
                ),
                "GF_LOG_LEVEL": "debug",
            },
        }

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-oauth2.yaml",
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
            name="grafana",
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            signing_key=create_test_cert(),
            redirect_uris="http://localhost:3000/",
            authorization_flow=authorization_flow,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        Application.objects.create(
            name="Grafana",
            slug=self.app_slug,
            provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
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
        "default/flow-default-provider-authorization-implicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-oauth2.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_authorization_consent_implied(self):
        """test OpenID Provider flow (default authorization flow with implied consent)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name="grafana",
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            signing_key=create_test_cert(),
            redirect_uris="http://localhost:3000/login/generic_oauth",
            authorization_flow=authorization_flow,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        Application.objects.create(
            name="Grafana",
            slug=self.app_slug,
            provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.login()
        self.wait_for_url("http://localhost:3000/?orgId=1")
        self.driver.get("http://localhost:3000/profile")
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            self.user.name,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=name]").get_attribute("value"),
            self.user.name,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=email]").get_attribute("value"),
            self.user.email,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=login]").get_attribute("value"),
            self.user.email,
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
        "system/providers-oauth2.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_authorization_logout(self):
        """test OpenID Provider flow with logout"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-implicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name="grafana",
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            signing_key=create_test_cert(),
            redirect_uris="http://localhost:3000/login/generic_oauth",
            authorization_flow=authorization_flow,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        Application.objects.create(
            name="Grafana",
            slug=self.app_slug,
            provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.login()
        self.wait_for_url("http://localhost:3000/?orgId=1")
        self.driver.get("http://localhost:3000/profile")
        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            self.user.name,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=name]").get_attribute("value"),
            self.user.name,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=email]").get_attribute("value"),
            self.user.email,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=login]").get_attribute("value"),
            self.user.email,
        )
        self.driver.get("http://localhost:3000/logout")
        self.wait_for_url(
            self.url(
                "authentik_core:if-session-end",
                application_slug=self.app_slug,
            )
        )
        self.driver.find_element(By.ID, "logout").click()

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-provider-authorization-explicit-consent.yaml",
    )
    @apply_blueprint(
        "system/providers-oauth2.yaml",
    )
    @reconcile_app("authentik_crypto")
    def test_authorization_consent_explicit(self):
        """test OpenID Provider flow (default authorization flow with explicit consent)"""
        sleep(1)
        # Bootstrap all needed objects
        authorization_flow = Flow.objects.get(
            slug="default-provider-authorization-explicit-consent"
        )
        provider = OAuth2Provider.objects.create(
            name="grafana",
            authorization_flow=authorization_flow,
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            signing_key=create_test_cert(),
            redirect_uris="http://localhost:3000/login/generic_oauth",
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        app = Application.objects.create(
            name="Grafana",
            slug=self.app_slug,
            provider=provider,
        )

        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.login()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-flow-executor")))
        sleep(1)

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

        self.wait_for_url("http://localhost:3000/?orgId=1")
        self.driver.get("http://localhost:3000/profile")

        self.assertEqual(
            self.driver.find_element(By.CLASS_NAME, "page-header__title").text,
            self.user.name,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=name]").get_attribute("value"),
            self.user.name,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=email]").get_attribute("value"),
            self.user.email,
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "input[name=login]").get_attribute("value"),
            self.user.email,
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
        "system/providers-oauth2.yaml",
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
            name="grafana",
            authorization_flow=authorization_flow,
            client_type=ClientTypes.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            signing_key=create_test_cert(),
            redirect_uris="http://localhost:3000/login/generic_oauth",
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        provider.save()
        app = Application.objects.create(
            name="Grafana",
            slug=self.app_slug,
            provider=provider,
        )

        negative_policy = ExpressionPolicy.objects.create(
            name="negative-static", expression="return False"
        )
        PolicyBinding.objects.create(target=app, policy=negative_policy, order=0)
        self.driver.get("http://localhost:3000")
        self.driver.find_element(By.CLASS_NAME, "btn-service--oauth").click()
        self.login()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "header > h1")))
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "header > h1").text,
            "Permission denied",
        )
