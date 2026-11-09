"""Test SAML SSO views"""

from base64 import b64encode
from urllib.parse import parse_qs, urlparse

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
)
from authentik.flows.models import Flow, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor
from authentik.stages.dummy.models import DummyStage

# (URL name, HTTP method) for each way an SP can send an AuthnRequest
BINDINGS = [
    ("sso-redirect", "get"),
    ("sso-post", "post"),
    ("base", "get"),
    ("base", "post"),
]


def create_flow_with_stage() -> Flow:
    """Create a flow that stops at a stage, so a redirect to it shows that it was planned"""
    flow = create_test_flow()
    FlowStageBinding.objects.create(
        target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
    )
    return flow


class TestSAMLSSOForceAuthn(TestCase):
    """ForceAuthn requires exactly one new login for each AuthnRequest"""

    def setUp(self):
        cert = create_test_cert()
        self.authentication_flow = create_flow_with_stage()
        self.authorization_flow = create_flow_with_stage()
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            authentication_flow=self.authentication_flow,
            authorization_flow=self.authorization_flow,
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=cert,
            verification_kp=cert,
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.application = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=provider
        )
        # Builds the AuthnRequests, the same way an SP would
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer_override="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=cert,
            verification_kp=cert,
            # Signs POST binding requests, which the provider requires
            binding_type=SAMLBindingTypes.POST,
            force_authn=True,
        )
        self.user = create_test_admin_user()

    def _send(self, url_name: str, method: str) -> tuple[HttpResponse, str]:
        """Send a new AuthnRequest, return the response and the URL that resumes it"""
        processor = RequestProcessor(self.source, RequestFactory().get("/"), generate_id())
        url = reverse(
            f"authentik_providers_saml:{url_name}",
            kwargs={"application_slug": self.application.slug},
        )
        if method == "post":
            data = {"SAMLRequest": b64encode(processor.build_auth_n().encode()).decode()}
            response = self.client.post(url, data)
        else:
            response = self.client.get(url, processor.build_auth_n_detached())
        return response, self._next(response)

    def _next(self, response: HttpResponse) -> str:
        return parse_qs(urlparse(response["Location"]).query).get("next", [""])[0]

    def assertRedirectsToFlow(self, response: HttpResponse, flow: Flow):
        """Check that the response starts `flow`"""
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response["Location"]).path,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}),
        )

    def test_logged_out(self):
        """A ForceAuthn request starting logged out only needs one login"""
        for url_name, method in BINDINGS:
            with self.subTest(url_name=url_name, method=method):
                self.client.logout()
                response, resume = self._send(url_name, method)
                self.assertRedirectsToFlow(response, self.authentication_flow)
                self.client.force_login(self.user)
                self.assertRedirectsToFlow(self.client.get(resume), self.authorization_flow)

    def test_repeated_requests(self):
        """Every ForceAuthn request requires a new login"""
        for url_name, method in BINDINGS:
            with self.subTest(url_name=url_name, method=method):
                self.client.logout()
                self.client.force_login(self.user)
                for _ in range(2):
                    response, resume = self._send(url_name, method)
                    self.assertRedirectsToFlow(response, self.authentication_flow)
                    # Returning without logging in cannot substitute for the login,
                    # and must not lose the request.
                    response = self.client.get(resume)
                    self.assertRedirectsToFlow(response, self.authentication_flow)
                    self.assertEqual(self._next(response), resume)
                    self.client.force_login(self.user)
                    self.assertRedirectsToFlow(self.client.get(resume), self.authorization_flow)

    def test_different_request(self):
        """A pending login for one AuthnRequest cannot satisfy a different one"""
        self.client.force_login(self.user)
        response, _ = self._send("sso-redirect", "get")
        self.assertRedirectsToFlow(response, self.authentication_flow)
        self.client.force_login(self.user)
        # Before the first request resumes, a different one starts.
        response, resume = self._send("sso-redirect", "get")
        self.assertRedirectsToFlow(response, self.authentication_flow)
        self.client.force_login(self.user)
        self.assertRedirectsToFlow(self.client.get(resume), self.authorization_flow)

    def test_without_force_authn(self):
        """An existing session is enough without ForceAuthn"""
        self.source.force_authn = False
        self.source.save()
        self.client.force_login(self.user)
        for url_name, method in BINDINGS:
            with self.subTest(url_name=url_name, method=method):
                response, _ = self._send(url_name, method)
                self.assertRedirectsToFlow(response, self.authorization_flow)
