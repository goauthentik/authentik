"""Test SAML provider ForceAuthn re-authentication

Regression tests for the SP-initiated ForceAuthn path: a logged-in session must be
bounced into the authentication flow, and the request must proceed once a fresh
login event exists in the session (https://github.com/goauthentik/authentik/issues/26861).
"""

from urllib.parse import urlparse

from django.test import TestCase
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
)
from authentik.events.signals import SESSION_LOGIN_EVENT
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.views.sso import SESSION_KEY_LAST_LOGIN_UID
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor
from authentik.stages.dummy.models import DummyStage


class TestSAMLForceAuthn(TestCase):
    """SP-initiated login with ForceAuthn re-authenticates a logged-in session,
    and proceeds once the user has logged in again"""

    @apply_blueprint("system/providers-saml.yaml")
    def setUp(self):
        self.request_factory = RequestFactory()
        self.cert = create_test_cert()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=create_test_flow(),
            authentication_flow=create_test_flow(FlowDesignation.AUTHENTICATION),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=self.cert,
            verification_kp=self.cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.provider.save()
        Application.objects.create(
            name="test-app",
            slug="test-app",
            provider=self.provider,
        )
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer_override="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=self.cert,
            verification_kp=self.cert,
            signed_assertion=True,
            binding_type=SAMLBindingTypes.POST,
        )
        # The planner refuses empty flows, so both flows need at least one stage
        for flow in (self.provider.authorization_flow, self.provider.authentication_flow):
            FlowStageBinding.objects.create(
                target=flow,
                stage=DummyStage.objects.create(name=generate_id()),
                order=0,
            )

    def _sso_url(self) -> str:
        """URL of the redirect-binding SSO endpoint for the test application"""
        return reverse(
            "authentik_providers_saml:sso-redirect",
            kwargs={"application_slug": "test-app"},
        )

    def _saml_request_params(self) -> dict:
        """Build SAMLRequest query parameters from the source, which acts as the SP"""
        http_request = self.request_factory.get("/")
        return RequestProcessor(self.source, http_request, "test_state").build_auth_n_detached()

    @staticmethod
    def _flow_slug(redirect_url: str) -> str:
        """Flow slug of an if-flow executor redirect URL"""
        return urlparse(redirect_url).path.rstrip("/").split("/")[-1]

    def test_force_authn_reauthenticates_logged_in_session(self):
        """A logged-in session is redirected into the authentication flow, and the
        login event present at that point is recorded for the re-login check"""
        self.source.force_authn = True
        self.source.save()
        self.client.force_login(create_test_admin_user())
        login_event = self.client.session.get(SESSION_LOGIN_EVENT)
        expected_uid = str(login_event.pk) if login_event else None

        response = self.client.get(self._sso_url(), self._saml_request_params())

        self.assertEqual(response.status_code, 302)
        # Redirected into the re-authentication flow, not the authorization flow
        self.assertEqual(self._flow_slug(response.url), self.provider.authentication_flow.slug)
        self.assertEqual(self.client.session.get(SESSION_KEY_LAST_LOGIN_UID), expected_uid)

    def test_force_authn_proceeds_after_relogin(self):
        """Once a fresh login event exists (the user re-authenticated, for example
        through an upstream source), the SAML request proceeds into the
        authorization flow"""
        self.source.force_authn = True
        self.source.save()
        user = create_test_admin_user()
        self.client.force_login(user)
        first_response = self.client.get(self._sso_url(), self._saml_request_params())
        self.assertEqual(
            self._flow_slug(first_response.url), self.provider.authentication_flow.slug
        )

        # Simulate the re-login completing in the same session: a new login event
        # is created, while the last seen login event UID stays untouched
        self.client.force_login(user)
        login_event = self.client.session.get(SESSION_LOGIN_EVENT)
        assert login_event is not None
        self.assertNotEqual(self.client.session[SESSION_KEY_LAST_LOGIN_UID], str(login_event.pk))

        response = self.client.get(self._sso_url(), self._saml_request_params())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self._flow_slug(response.url), self.provider.authorization_flow.slug)

    def test_without_force_authn_logged_in_session_proceeds(self):
        """Without ForceAuthn, a logged-in session proceeds directly into the
        authorization flow"""
        self.source.force_authn = False
        self.source.save()
        self.client.force_login(create_test_admin_user())

        response = self.client.get(self._sso_url(), self._saml_request_params())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self._flow_slug(response.url), self.provider.authorization_flow.slug)
        self.assertNotIn(SESSION_KEY_LAST_LOGIN_UID, self.client.session)
