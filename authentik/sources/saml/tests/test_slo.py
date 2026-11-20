"""SAML Source Single Logout view tests"""

from urllib.parse import parse_qs, urlparse

from django.test import TestCase
from django.urls import reverse

from authentik.core.tests.utils import create_test_brand, create_test_flow, create_test_user
from authentik.flows.models import FlowDesignation
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.views import PLAN_CONTEXT_SAML_RELAY_STATE

IDP_ENTITY_ID = "https://idp.example.com"
IDP_SLO_URL = "https://idp.example.com/slo"

LOGOUT_RESPONSE = f"""<samlp:LogoutResponse xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_response" Version="2.0"
    IssueInstant="2026-01-01T00:00:00Z" InResponseTo="_request">
    <saml:Issuer>{IDP_ENTITY_ID}</saml:Issuer>
    <samlp:Status>
        <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </samlp:Status>
</samlp:LogoutResponse>"""

LOGOUT_REQUEST = f"""<samlp:LogoutRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_idp_request" Version="2.0"
    IssueInstant="2026-01-01T00:00:00Z">
    <saml:Issuer>{IDP_ENTITY_ID}</saml:Issuer>
    <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
        user@example.com
    </saml:NameID>
    <samlp:SessionIndex>_session_index</samlp:SessionIndex>
</samlp:LogoutRequest>"""


class TestSLOView(TestCase):
    """Test the SAML source SLO view for IdP-initiated logout and LogoutResponse handling"""

    def setUp(self):
        # The test brand has no invalidation flow, so logouts complete without a flow
        self.brand = create_test_brand()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer_override=IDP_ENTITY_ID,
            slo_url=IDP_SLO_URL,
            pre_authentication_flow=create_test_flow(),
        )
        self.url = reverse("authentik_sources_saml:slo", kwargs={"source_slug": self.source.slug})

    def assert_logout_response_sent(self, response):
        """Assert that the view redirected to the IdP's SLO URL carrying a LogoutResponse"""
        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.url)
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}", IDP_SLO_URL)
        self.assertIn("SAMLResponse", parse_qs(parsed.query))

    def test_logout_response_without_session_continues_flow(self):
        """The IdP's LogoutResponse arrives after the local session has already been ended
        by the UserLogoutStage, so the view must process it without requiring a login and
        send the browser back into the invalidation flow"""
        relay_state = "https://authentik.example.com/if/flow/invalidation/"
        plan = FlowPlan(flow_pk=create_test_flow(FlowDesignation.INVALIDATION).pk.hex)
        plan.context[PLAN_CONTEXT_SAML_RELAY_STATE] = relay_state
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            self.url,
            {
                "SAMLResponse": deflate_and_base64_encode(LOGOUT_RESPONSE),
                "RelayState": relay_state,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, relay_state)

    def test_logout_request_without_session_is_answered(self):
        """An IdP-initiated LogoutRequest for a browser without a local session is still
        answered with a LogoutResponse instead of being redirected to the login page"""
        response = self.client.get(
            self.url, {"SAMLRequest": deflate_and_base64_encode(LOGOUT_REQUEST)}
        )
        self.assert_logout_response_sent(response)

    def test_logout_request_with_session_logs_out(self):
        """An IdP-initiated LogoutRequest ends the local session and is answered"""
        user = create_test_user()
        self.client.force_login(user)

        response = self.client.get(
            self.url, {"SAMLRequest": deflate_and_base64_encode(LOGOUT_REQUEST)}
        )
        self.assert_logout_response_sent(response)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_initiate_logout_requires_session(self):
        """Starting SP-initiated logout without a local session does nothing"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("authentik_core:root-redirect"))
