"""Test IdP Logout Stages"""

import base64
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_flow
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.providers.saml.idp_logout import (
    IframeLogoutChallenge,
    IframeLogoutStageView,
    SAMLLogoutChallenge,
    SAMLLogoutStageView,
)
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS,
    SESSION_KEY_SAML_LOGOUT_RETURN,
)
from authentik.sources.saml.processors.constants import (
    RSA_SHA256,
    SAML_NAME_ID_FORMAT_EMAIL,
)


class TestSAMLLogoutStageView(TestCase):
    """Test SAMLLogoutStageView (redirect chain logout)"""

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
            logout_method="frontchannel_redirect",
        )

        self.provider2 = SAMLProvider.objects.create(
            name="test-provider-2",
            authorization_flow=self.flow,
            acs_url="https://sp2.example.com/acs",
            sls_url="https://sp2.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="post",
            sls_binding="post",
            logout_method="frontchannel_redirect",
        )

    def test_encode_decode_relay_state(self):
        """Test relay state encoding and decoding"""
        request = self.factory.get("/")
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        stage_view = SAMLLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )
        original_url = "https://idp.example.com/flow/return"

        # Test encoding
        encoded = stage_view.encode_relay_state(original_url)

        # Test decoding
        decoded = stage_view.decode_relay_state(encoded)
        self.assertEqual(decoded, original_url)

        # Test invalid relay state
        invalid_decoded = stage_view.decode_relay_state("invalid-base64!@#")
        self.assertEqual(invalid_decoded, "")

    def test_get_challenge_with_pending_providers_redirect(self):
        """Test get_challenge when there are pending providers with redirect binding"""
        request = self.factory.get("/")
        request.session = {}
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = [
            {
                "provider_pk": str(self.provider1.pk),
                "name_id": "user1@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-123",
            }
        ]
        stage_view = SAMLLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return a SAMLLogoutChallenge
        self.assertIsInstance(challenge, SAMLLogoutChallenge)
        self.assertEqual(challenge.initial_data["binding"], "redirect")
        self.assertEqual(challenge.initial_data["provider_name"], "test-provider-1")
        self.assertIn("redirect_url", challenge.initial_data)

        # Should have removed the provider from pending list
        self.assertEqual(len(plan.context.get(PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS, [])), 0)

        # Should have stored return URL in session
        self.assertEqual(
            request.session[SESSION_KEY_SAML_LOGOUT_RETURN],
            "https://idp.example.com/flow/test-flow",
        )

    def test_get_challenge_with_pending_providers_post(self):
        """Test get_challenge when there are pending providers with POST binding"""
        request = self.factory.get("/")
        request.session = {}
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = [
            {
                "provider_pk": str(self.provider2.pk),
                "name_id": "user2@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-456",
            }
        ]
        stage_view = SAMLLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return a SAMLLogoutChallenge
        self.assertIsInstance(challenge, SAMLLogoutChallenge)
        self.assertEqual(challenge.initial_data["binding"], "post")
        self.assertEqual(challenge.initial_data["provider_name"], "test-provider-2")
        self.assertEqual(challenge.initial_data["url"], self.provider2.sls_url)
        self.assertIn("saml_request", challenge.initial_data)
        self.assertIn("relay_state", challenge.initial_data)

    def test_get_challenge_all_complete(self):
        """Test get_challenge when all providers are done"""
        request = self.factory.get("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = []  # No pending providers
        stage_view = SAMLLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        challenge = stage_view.get_challenge()

        # Should return completion challenge
        self.assertIsInstance(challenge, SAMLLogoutChallenge)
        self.assertEqual(challenge.initial_data["is_complete"], True)

    def test_get_challenge_provider_not_found(self):
        """Test get_challenge when provider doesn't exist"""
        request = self.factory.get("/")
        request.session = {}
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = [
            {
                "provider_pk": "999999",  # Non-existent provider
                "name_id": "user@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-789",
            }
        ]
        stage_view = SAMLLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        with patch("authentik.providers.saml.idp_logout.LOGGER") as mock_logger:
            challenge = stage_view.get_challenge()

            # Should log error and skip to completion
            mock_logger.error.assert_called()

            # Should return completion since no valid providers
            self.assertEqual(challenge.initial_data["is_complete"], True)

    def test_challenge_valid_continues_flow(self):
        """Test challenge_valid continues to next provider or completes"""
        request = self.factory.post("/")
        request.session = {}

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = []
        executor = FlowExecutorView(
            request=request,
            flow=self.flow,
            plan=plan,
        )
        executor.stage_ok = Mock(return_value=Mock(status_code=200))

        stage_view = SAMLLogoutStageView(executor, request=request)

        # Mock get_challenge to return completion
        stage_view.get_challenge = Mock()
        completion_challenge = SAMLLogoutChallenge(data={"is_complete": True})
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
                "provider_pk": str(self.provider1.pk),
                "name_id": "user@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-123",
            },
            {
                "provider_pk": str(self.provider2.pk),
                "name_id": "user@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-456",
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
        self.assertIn("relay_state", logout_urls[1])

    def test_get_challenge_with_provider_error(self):
        """Test get_challenge handles provider errors gracefully"""
        request = self.factory.get("/")
        request.session = {}
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = [
            {
                "provider_pk": "999999",  # Non-existent provider
                "name_id": "user@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-789",
            },
            {
                "provider_pk": str(self.provider1.pk),
                "name_id": "user@example.com",
                "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
                "session_index": "session-123",
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

        with patch("authentik.providers.saml.idp_logout.LOGGER") as mock_logger:
            challenge = stage_view.get_challenge()

            # Should log warning for failed provider
            mock_logger.warning.assert_called()

            # Should still return valid logout URLs
            logout_urls = challenge.initial_data["logout_urls"]
            self.assertEqual(len(logout_urls), 1)  # Only valid provider
            self.assertEqual(logout_urls[0]["provider_name"], "test-provider-1")

    def test_challenge_valid_completes_stage(self):
        """Test challenge_valid completes the stage"""
        request = self.factory.post("/")
        request.session = {SESSION_KEY_SAML_LOGOUT_RETURN: "test"}

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

        # Should clear the session key
        self.assertNotIn(SESSION_KEY_SAML_LOGOUT_RETURN, request.session)

    def test_process_session_for_logout_redirect(self):
        """Test _process_session_for_logout with redirect binding"""
        request = self.factory.get("/")
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        stage_view = IframeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        session_data = {
            "provider_pk": str(self.provider1.pk),
            "name_id": "user@example.com",
            "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
            "session_index": "session-123",
        }

        result = stage_view._process_session_for_logout(
            session_data, user=None, return_url="https://idp.example.com/flow/test-flow"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["provider_name"], "test-provider-1")
        self.assertEqual(result["binding"], "redirect")
        self.assertIn("url", result)

    def test_process_session_for_logout_post(self):
        """Test _process_session_for_logout with POST binding"""
        request = self.factory.get("/")
        request.build_absolute_uri = Mock(return_value="https://idp.example.com/flow/test-flow")

        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        stage_view = IframeLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        session_data = {
            "provider_pk": str(self.provider2.pk),
            "name_id": "user@example.com",
            "name_id_format": SAML_NAME_ID_FORMAT_EMAIL,
            "session_index": "session-456",
        }

        result = stage_view._process_session_for_logout(
            session_data, user=None, return_url="https://idp.example.com/flow/test-flow"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["provider_name"], "test-provider-2")
        self.assertEqual(result["binding"], "post")
        self.assertEqual(result["url"], self.provider2.sls_url)
        self.assertIn("saml_request", result)
        self.assertIn("relay_state", result)


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
            logout_method="frontchannel_redirect",
        )

    def test_relay_state_preservation(self):
        """Test that relay state is properly encoded and preserved"""
        request = self.factory.get("/")
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        stage_view = SAMLLogoutStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
                plan=plan,
            ),
            request=request,
        )

        # Test various URL formats
        test_urls = [
            "https://idp.example.com/flow/test",
            "https://idp.example.com/flow/test?param=value",
            "https://idp.example.com/flow/test#fragment",
            "/relative/path",
        ]

        for url in test_urls:
            encoded = stage_view.encode_relay_state(url)
            decoded = stage_view.decode_relay_state(encoded)
            self.assertEqual(decoded, url, f"Failed for URL: {url}")

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
