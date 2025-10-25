"""Test SP-initiated SAML Single Logout Views"""

from unittest.mock import MagicMock, patch

from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_brand, create_test_flow
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.views.flows import PLAN_CONTEXT_SAML_RELAY_STATE
from authentik.providers.saml.views.sp_slo import (
    SPInitiatedSLOBindingPOSTView,
    SPInitiatedSLOBindingRedirectView,
)
from authentik.sources.saml.processors.constants import SAML_NAME_ID_FORMAT_EMAIL


class TestSPInitiatedSLOViews(TestCase):
    """Test SP-initiated SAML Single Logout Views"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.brand = create_test_brand()
        self.flow = create_test_flow()
        self.invalidation_flow = create_test_flow()

        # Create provider
        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            invalidation_flow=self.invalidation_flow,
            acs_url="https://sp.example.com/acs",
            sls_url="https://sp.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="redirect",
            sls_binding="redirect",
        )

        # Create application
        self.application = Application.objects.create(
            name="test-app",
            slug="test-app",
            provider=self.provider,
        )

        # Create logout request processor for generating test requests
        self.processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://idp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state="https://sp.example.com/return",
        )

    def test_redirect_view_handles_logout_request(self):
        """Test that redirect view properly handles a logout request"""
        # Generate encoded logout request
        encoded_request = self.processor.encode_redirect()

        # Create request with SAML logout request
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLRequest": encoded_request,
                "RelayState": "https://sp.example.com/return",
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        view.resolve_provider_application()

        # Check that the SAML request is parsed correctly
        result = view.check_saml_request()
        self.assertIsNone(result)  # None means success

        # Verify logout request was stored in plan context
        self.assertIn("authentik/providers/saml/logout_request", view.plan_context)
        logout_request = view.plan_context["authentik/providers/saml/logout_request"]
        self.assertEqual(logout_request.issuer, self.provider.issuer)
        self.assertEqual(logout_request.session_index, "test-session-123")

    def test_redirect_view_handles_logout_response_with_relay_state(self):
        """Test that redirect view handles logout response with RelayState"""
        # Use raw URL (no encoding needed)
        relay_state = "https://idp.example.com/flow/return"

        # Create request with SAML logout response
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
                "RelayState": relay_state,
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should redirect to relay state URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, relay_state)

    def test_redirect_view_handles_logout_response_plain_relay_state(self):
        """Test that redirect view handles logout response with plain RelayState"""
        relay_state = "https://sp.example.com/plain"

        # Create request with SAML logout response
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
                "RelayState": relay_state,
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should redirect to plain relay state
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, relay_state)

    def test_redirect_view_handles_logout_response_no_relay_state_with_plan_context(self):
        """Test that redirect view uses plan context fallback when no RelayState"""
        relay_state = "https://idp.example.com/flow/plan-return"

        # Create request with SAML logout response
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
            },
        )
        # Create a flow plan with the return URL
        plan = FlowPlan(flow_pk="test-flow")
        plan.context[PLAN_CONTEXT_SAML_RELAY_STATE] = relay_state
        request.session = {SESSION_KEY_PLAN: plan}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should redirect to plan context stored URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, relay_state)

    def test_redirect_view_handles_logout_response_no_relay_state_no_session(self):
        """Test that redirect view uses root redirect as final fallback"""
        # Create request with SAML logout response
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should redirect to root-redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("authentik_core:root-redirect"))

    def test_redirect_view_missing_saml_request(self):
        """Test redirect view when SAML request is missing"""
        request = self.factory.get(f"/slo/redirect/{self.application.slug}/")
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        view.resolve_provider_application()

        # Should return error response
        result = view.check_saml_request()
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)

    def test_post_view_handles_logout_request(self):
        """Test that POST view properly handles a logout request"""
        # Generate encoded logout request
        encoded_request = self.processor.encode_post()

        # Create POST request with SAML logout request
        request = self.factory.post(
            f"/slo/post/{self.application.slug}/",
            {
                "SAMLRequest": encoded_request,
                "RelayState": "https://sp.example.com/return",
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingPOSTView()
        view.setup(request, application_slug=self.application.slug)
        view.resolve_provider_application()

        # Check that the SAML request is parsed correctly
        result = view.check_saml_request()
        self.assertIsNone(result)  # None means success

        # Verify logout request was stored in plan context
        self.assertIn("authentik/providers/saml/logout_request", view.plan_context)
        logout_request = view.plan_context["authentik/providers/saml/logout_request"]
        self.assertEqual(logout_request.issuer, self.provider.issuer)
        self.assertEqual(logout_request.session_index, "test-session-123")

    def test_post_view_handles_logout_response_with_relay_state(self):
        """Test that POST view handles logout response with RelayState"""
        # Use raw URL (no encoding needed)
        relay_state = "https://idp.example.com/flow/return"

        # Create POST request with SAML logout response
        request = self.factory.post(
            f"/slo/post/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
                "RelayState": relay_state,
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingPOSTView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should redirect to relay state URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, relay_state)

    def test_post_view_handles_logout_response_no_relay_state_with_plan_context(self):
        """Test that POST view uses plan context fallback when no RelayState"""
        relay_state = "https://idp.example.com/flow/plan-return"

        # Create POST request with SAML logout response
        request = self.factory.post(
            f"/slo/post/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
            },
        )
        # Create a flow plan with the return URL
        plan = FlowPlan(flow_pk="test-flow")
        plan.context[PLAN_CONTEXT_SAML_RELAY_STATE] = relay_state
        request.session = {SESSION_KEY_PLAN: plan}
        request.brand = self.brand

        view = SPInitiatedSLOBindingPOSTView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should redirect to plan context stored URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, relay_state)

    def test_post_view_missing_saml_request(self):
        """Test POST view when SAML request is missing"""
        request = self.factory.post(f"/slo/post/{self.application.slug}/", {})
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingPOSTView()
        view.setup(request, application_slug=self.application.slug)
        view.resolve_provider_application()

        # Should return error response
        result = view.check_saml_request()
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)

    @patch("authentik.providers.saml.views.sp_slo.LOGGER")
    @patch("authentik.providers.saml.views.sp_slo.Event")
    @patch("authentik.providers.saml.views.sp_slo.LogoutRequestParser")
    def test_redirect_view_handles_parser_exception(
        self, mock_parser_class, mock_event_class, mock_logger
    ):
        """Test redirect view handles parser exception gracefully"""
        # Mock Event.new to avoid the error
        mock_event = MagicMock()
        mock_event.save = MagicMock()
        mock_event_class.new.return_value = mock_event

        # Mock LOGGER.error to avoid the error
        mock_logger.error = MagicMock()

        # Make parser raise exception
        mock_parser = MagicMock()
        mock_parser.parse_detached.side_effect = CannotHandleAssertion("Invalid request")
        mock_parser_class.return_value = mock_parser

        # Create request with SAML logout request
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLRequest": "invalid-request",
                "RelayState": "test",
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        view.resolve_provider_application()

        # Should return error response
        result = view.check_saml_request()
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)

    @patch("authentik.providers.saml.views.sp_slo.LOGGER")
    @patch("authentik.providers.saml.views.sp_slo.Event")
    @patch("authentik.providers.saml.views.sp_slo.LogoutRequestParser")
    def test_post_view_handles_parser_exception(
        self, mock_parser_class, mock_event_class, mock_logger
    ):
        """Test POST view handles parser exception gracefully"""
        # Mock Event.new to avoid the error
        mock_event = MagicMock()
        mock_event.save = MagicMock()
        mock_event_class.new.return_value = mock_event

        # Mock LOGGER.error to avoid the error
        mock_logger.error = MagicMock()

        # Make parser raise exception
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = CannotHandleAssertion("Invalid request")
        mock_parser_class.return_value = mock_parser

        # Create POST request with SAML logout request
        request = self.factory.post(
            f"/slo/post/{self.application.slug}/",
            {
                "SAMLRequest": "invalid-request",
                "RelayState": "test",
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingPOSTView()
        view.setup(request, application_slug=self.application.slug)
        view.resolve_provider_application()

        # Should return error response
        result = view.check_saml_request()
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)

    def test_application_not_found(self):
        """Test handling when application doesn't exist"""
        request = self.factory.get("/slo/redirect/non-existent/")
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug="non-existent")

        with self.assertRaises(Http404):
            view.resolve_provider_application()

    def test_provider_without_invalidation_flow(self):
        """Test handling when provider has no invalidation flow and brand has no default"""
        # Create provider without invalidation flow
        provider = SAMLProvider.objects.create(
            name="no-flow-provider",
            authorization_flow=self.flow,
            acs_url="https://sp2.example.com/acs",
            sls_url="https://sp2.example.com/sls",
            issuer="https://idp2.example.com",
            invalidation_flow=None,  # No invalidation flow
        )

        app = Application.objects.create(
            name="no-flow-app",
            slug="no-flow-app",
            provider=provider,
        )

        # Brand with no flow_invalidation
        self.brand.flow_invalidation = None
        self.brand.save()

        request = self.factory.get(f"/slo/redirect/{app.slug}/")
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=app.slug)

        with self.assertRaises(Http404):
            view.resolve_provider_application()

    def test_relay_state_decoding_failure(self):
        """Test handling of RelayState that's a path"""
        # Create request with relay state that is a path
        request = self.factory.get(
            f"/slo/redirect/{self.application.slug}/",
            {
                "SAMLResponse": "dummy-response",
                "RelayState": "/some/invalid/path",  # Use a path that starts with /
            },
        )
        request.session = {}
        request.brand = self.brand

        view = SPInitiatedSLOBindingRedirectView()
        view.setup(request, application_slug=self.application.slug)
        response = view.dispatch(request, application_slug=self.application.slug)

        # Should treat it as plain URL and redirect to it
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/some/invalid/path")
