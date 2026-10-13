"""Test SAML provider ForceAuthn re-authentication"""

from django.test import TestCase
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_cert,
    create_test_flow,
    create_test_user,
)
from authentik.events.signals import SESSION_LOGIN_EVENT
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.views.sso import SESSION_KEY_LAST_LOGIN_UID
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor
from authentik.stages.dummy.models import DummyStage


class TestSAMLForceAuthn(TestCase):
    """SP-initiated SSO with ForceAuthn for a logged-in session"""

    @apply_blueprint("system/providers-saml.yaml")
    def setUp(self):
        cert = create_test_cert()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=create_test_flow(),
            authentication_flow=create_test_flow(FlowDesignation.AUTHENTICATION),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=cert,
            verification_kp=cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        Application.objects.create(name="test-app", slug="test-app", provider=self.provider)
        # The planner refuses an empty authentication flow, and an empty authorization flow
        # skips its executor and redirects straight to the ACS URL. A stage in each keeps
        # the response a redirect to the flow the request was sent to.
        for flow in (self.provider.authentication_flow, self.provider.authorization_flow):
            FlowStageBinding.objects.create(
                target=flow,
                stage=DummyStage.objects.create(name=generate_id()),
                order=0,
            )
        # The source builds the AuthnRequest, acting as the SP
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer_override="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=cert,
            verification_kp=cert,
        )
        self.user = create_test_user()

    def sso(self, force_authn: bool = True):
        """Send an AuthnRequest to the redirect-binding SSO endpoint"""
        self.source.force_authn = force_authn
        params = RequestProcessor(
            self.source, RequestFactory().get("/"), generate_id()
        ).build_auth_n_detached()
        return self.client.get(
            reverse(
                "authentik_providers_saml:sso-redirect",
                kwargs={"application_slug": "test-app"},
            ),
            params,
        )

    def assertRedirectsToFlow(self, response, flow: Flow):
        """Assert that `response` redirects to the flow executor for `flow`"""
        self.assertEqual(response.status_code, 302)
        flow_url = reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        self.assertTrue(response.url.startswith(flow_url), response.url)

    def test_force_authn_reauthenticates(self):
        """A logged-in session is sent to the authentication flow, and its current login
        event is recorded"""
        self.client.force_login(self.user)

        response = self.sso()

        self.assertRedirectsToFlow(response, self.provider.authentication_flow)
        self.assertEqual(
            self.client.session[SESSION_KEY_LAST_LOGIN_UID],
            str(self.client.session[SESSION_LOGIN_EVENT].pk),
        )

    def test_force_authn_without_relogin(self):
        """Repeating the request without logging in again doesn't skip re-authentication"""
        self.client.force_login(self.user)
        self.sso()

        response = self.sso()

        self.assertRedirectsToFlow(response, self.provider.authentication_flow)

    def test_force_authn_after_relogin(self):
        """Once the user has logged in again, the request continues to the authorization
        flow"""
        self.client.force_login(self.user)
        self.sso()
        self.client.force_login(self.user)

        response = self.sso()

        self.assertRedirectsToFlow(response, self.provider.authorization_flow)

    def test_no_force_authn(self):
        """Without ForceAuthn, a logged-in session continues to the authorization flow"""
        self.client.force_login(self.user)

        response = self.sso(force_authn=False)

        self.assertRedirectsToFlow(response, self.provider.authorization_flow)
        self.assertNotIn(SESSION_KEY_LAST_LOGIN_UID, self.client.session)
