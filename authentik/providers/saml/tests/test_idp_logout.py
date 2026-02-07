"""Test IdP Logout Stages"""

import base64
from unittest.mock import Mock

from django.test import RequestFactory, TestCase

from authentik.common.oauth.constants import (
    OAUTH2_BINDING,
    PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS,
)
from authentik.common.saml.constants import (
    RSA_SHA256,
    SAML_NAME_ID_FORMAT_EMAIL,
)
from authentik.core.tests.utils import create_test_flow
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.providers.iframe_logout import (
    IframeLogoutChallenge,
    IframeLogoutStageView,
)
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.saml.models import SAMLLogoutMethods, SAMLProvider
from authentik.providers.saml.native_logout import (
    NativeLogoutChallenge,
    NativeLogoutStageView,
)
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS,
)


class TestNativeLogoutStageView(TestCase):
    """Test NativeLogoutStageView (redirect chain logout)"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.flow = create_test_flow()

        # Create test providers
        self.provider1 = SAMLProvider.objects.create(
            name="test-provider-1",
            authorization_flow=self.flow,
            acs_url="https://sp1.example.com/acs",
            sls_url="https://sp1.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="redirect",
            sls_binding="redirect",
            logout_method=SAMLLogoutMethods.FRONTCHANNEL_NATIVE,
        )

        self.provider2 = SAMLProvider.objects.create(
            name="test-provider-2",
            authorization_flow=self.flow,
            acs_url="https://sp2.example.com/acs",
            sls_url="https://sp2.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="post",
            sls_binding="post",
            logout_method=SAMLLogoutMethods.FRONTCHANNEL_NATIVE,
        )

    def test_get_challenge_with_pending_providers_redirect(self):
        """Test get_challenge when there are pending providers with redirect binding"""
        request = self.factory.get("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = [
            {
                "redirect_url": "https://sp1.example.com/sls?SAMLRequest=encoded",
                "provider_name": "test-provider-1",
                "binding": "redirect",
            }
        ]
        stage_view = NativeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return a NativeLogoutChallenge
        self.assertIsInstance(challenge, NativeLogoutChallenge)
        self.assertEqual(challenge.initial_data["binding"], "redirect")
        self.assertEqual(challenge.initial_data["provider_name"], "test-provider-1")
        self.assertIn("redirect_url", challenge.initial_data)

        # Should have removed the provider from pending list
        self.assertEqual(len(plan.context.get(PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS, [])), 0)

    def test_get_challenge_with_pending_providers_post(self):
        """Test get_challenge when there are pending providers with POST binding"""
        request = self.factory.get("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = [
            {
                "post_url": "https://sp2.example.com/sls",
                "saml_request": "encoded_saml_request",
                "relay_state": "https://idp.example.com/flow/test-flow",
                "provider_name": "test-provider-2",
                "binding": "post",
            }
        ]
        stage_view = NativeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return a NativeLogoutChallenge
        self.assertIsInstance(challenge, NativeLogoutChallenge)
        self.assertEqual(challenge.initial_data["binding"], "post")
        self.assertEqual(challenge.initial_data["provider_name"], "test-provider-2")
        self.assertEqual(challenge.initial_data["post_url"], "https://sp2.example.com/sls")
        self.assertIn("saml_request", challenge.initial_data)
        self.assertIn("relay_state", challenge.initial_data)

    def test_get_challenge_all_complete(self):
        """Test get_challenge when all providers are done"""
        request = self.factory.get("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = []  # No pending providers
        stage_view = NativeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return completion challenge
        self.assertIsInstance(challenge, NativeLogoutChallenge)
        self.assertEqual(challenge.initial_data["is_complete"], True)

    def test_get_challenge_with_empty_sessions(self):
        """Test get_challenge when sessions list is empty"""
        request = self.factory.get("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = []
        stage_view = NativeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return completion challenge
        self.assertIsInstance(challenge, NativeLogoutChallenge)
        self.assertEqual(challenge.initial_data["is_complete"], True)

    def test_challenge_valid_continues_flow(self):
        """Test challenge_valid continues to next provider or completes"""
        request = self.factory.post("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = []
        executor = FlowExecutorView(
            request=request,
            flow=self.flow,
            plan=plan,
        )
        executor.stage_ok = Mock(return_value=Mock(status_code=200))

        stage_view = NativeLogoutStageView(executor, request=request)

        # Mock get_challenge to return completion
        stage_view.get_challenge = Mock()
        completion_challenge = NativeLogoutChallenge(data={"is_complete": True})
        completion_challenge.is_valid()
        stage_view.get_challenge.return_value = completion_challenge

        response = Mock()
        stage_view.challenge_valid(response)

        # Should call stage_ok when complete and return its value
        executor.stage_ok.assert_called_once()


class TestIframeLogoutStageView(TestCase):
    """Test IframeLogoutStageView (parallel iframe logout)"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.flow = create_test_flow()

        # Create test providers
        self.provider1 = SAMLProvider.objects.create(
            name="test-provider-1",
            authorization_flow=self.flow,
            acs_url="https://sp1.example.com/acs",
            sls_url="https://sp1.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="redirect",
            sls_binding="redirect",
            logout_method="frontchannel_iframe",
        )

        self.provider2 = SAMLProvider.objects.create(
            name="test-provider-2",
            authorization_flow=self.flow,
            acs_url="https://sp2.example.com/acs",
            sls_url="https://sp2.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="post",
            sls_binding="post",
            logout_method="frontchannel_iframe",
        )

    def test_get_challenge_with_multiple_providers(self):
        """Test get_challenge generates logout URLs for all providers"""
        request = self.factory.get("/")
        request.session = {}
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = [
            {
                "url": "https://sp1.example.com/sls?SAMLRequest=encoded1",
                "provider_name": "test-provider-1",
                "binding": "redirect",
            },
            {
                "url": "https://sp2.example.com/sls",
                "saml_request": "encoded2",
                "provider_name": "test-provider-2",
                "binding": "post",
            },
        ]
        stage_view = IframeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return iframe challenge with logout URLs
        self.assertIsInstance(challenge, IframeLogoutChallenge)
        logout_urls = challenge.initial_data["logout_urls"]

        # Should have 2 logout URLs
        self.assertEqual(len(logout_urls), 2)

        # Check first provider (redirect binding)
        self.assertEqual(logout_urls[0]["provider_name"], "test-provider-1")
        self.assertEqual(logout_urls[0]["binding"], "redirect")
        self.assertIn("url", logout_urls[0])

        # Check second provider (post binding)
        self.assertEqual(logout_urls[1]["provider_name"], "test-provider-2")
        self.assertEqual(logout_urls[1]["binding"], "post")
        self.assertEqual(logout_urls[1]["url"], self.provider2.sls_url)
        self.assertIn("saml_request", logout_urls[1])

    def test_get_challenge_with_mixed_sessions(self):
        """Test get_challenge with both SAML and OIDC sessions"""
        request = self.factory.get("/")
        request.session = {}
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        # SAML sessions (pre-processed)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = [
            {
                "url": "https://sp1.example.com/sls?SAMLRequest=encoded1",
                "provider_name": "test-provider-1",
                "binding": "redirect",
            },
        ]
        # OIDC sessions (pre-processed)
        plan.context[PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS] = [
            {
                "url": "https://oidc.example.com/logout?iss=authentik&sid=abc123",
                "provider_name": "oidc-provider",
                "binding": OAUTH2_BINDING,
                "provider_type": (
                    f"{OAuth2Provider._meta.app_label}" f".{OAuth2Provider._meta.model_name}"
                ),
            },
        ]
        stage_view = IframeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return iframe challenge with logout URLs from both SAML and OIDC
        logout_urls = challenge.initial_data["logout_urls"]
        self.assertEqual(len(logout_urls), 2)  # 1 SAML + 1 OIDC
        self.assertEqual(logout_urls[0]["provider_name"], "test-provider-1")
        self.assertEqual(logout_urls[1]["provider_name"], "oidc-provider")

    def test_challenge_valid_completes_stage(self):
        """Test challenge_valid completes the stage"""
        request = self.factory.post("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = []
        executor = FlowExecutorView(
            request=request,
            flow=self.flow,
            plan=plan,
        )
        executor.stage_ok = Mock(return_value=Mock(status_code=200))

        stage_view = IframeLogoutStageView(executor, request=request)

        response = Mock()
        stage_view.challenge_valid(response)

        # Should call stage_ok
        executor.stage_ok.assert_called_once()

        # Session should remain empty (no session storage anymore)
        self.assertEqual(request.session, {})


class TestIdPLogoutIntegration(FlowTestCase):
    """Integration tests for IdP logout flow"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.factory = RequestFactory()
        self.flow = create_test_flow()

        # Create test provider with signing
        from authentik.core.tests.utils import create_test_cert

        self.keypair = create_test_cert()

        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            acs_url="https://sp.example.com/acs",
            sls_url="https://sp.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="redirect",
            sls_binding="redirect",
            signing_kp=self.keypair,
            sign_logout_request=True,
            signature_algorithm=RSA_SHA256,
            logout_method=SAMLLogoutMethods.FRONTCHANNEL_NATIVE,
        )

    def test_signed_logout_request_generation(self):
        """Test that signed logout requests are generated correctly"""
        from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor

        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination=self.provider.sls_url,
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session",
            relay_state=base64.urlsafe_b64encode(b"https://idp.example.com/return").decode(),
        )

        # Test redirect URL includes signature
        redirect_url = processor.get_redirect_url()
        self.assertIn("Signature=", redirect_url)
        self.assertIn("SigAlg=", redirect_url)

        # Test POST data is signed
        post_data = processor.get_post_form_data()
        self.assertIn("SAMLRequest", post_data)

        # Decode and check for signature in XML
        from lxml import etree

        decoded = base64.b64decode(post_data["SAMLRequest"])
        root = etree.fromstring(decoded)
        signature = root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        self.assertIsNotNone(signature)
