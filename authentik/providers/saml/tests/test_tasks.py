"""Tests for SAML provider tasks"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from requests.exceptions import ConnectionError, HTTPError

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.tasks import (
    send_post_logout_request,
    send_saml_logout_request,
    send_saml_logout_response,
)
from authentik.sources.saml.processors.constants import SAML_NAME_ID_FORMAT_EMAIL


class TestSendSamlLogoutResponse(TestCase):
    """Tests for send_saml_logout_response task"""

    def setUp(self):
        """Set up test fixtures"""
        self.cert = create_test_cert()
        self.flow = create_test_flow()

        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            acs_url="https://sp.example.com/acs",
            sls_url="https://sp.example.com/sls",
            issuer="https://idp.example.com",
            signing_kp=self.cert,
        )

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_successful_logout_response(self, mock_post):
        """Test successful POST to SP returns True"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = send_saml_logout_response(
            provider_pk=self.provider.pk,
            sls_url=self.provider.sls_url,
            logout_request_id="test-request-id",
            relay_state="https://sp.example.com/return",
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify the POST was made with correct data
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["timeout"], 10)
        self.assertEqual(
            call_kwargs["headers"]["Content-Type"], "application/x-www-form-urlencoded"
        )

        # Verify form data contains SAMLResponse and RelayState
        form_data = call_kwargs["data"]
        self.assertIn("SAMLResponse", form_data)
        self.assertIn("RelayState", form_data)
        self.assertEqual(form_data["RelayState"], "https://sp.example.com/return")

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_successful_logout_response_no_relay_state(self, mock_post):
        """Test successful POST without relay_state"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = send_saml_logout_response(
            provider_pk=self.provider.pk,
            sls_url=self.provider.sls_url,
            logout_request_id="test-request-id",
            relay_state=None,
        )

        self.assertTrue(result)

        # Verify form data does not contain RelayState
        form_data = mock_post.call_args[1]["data"]
        self.assertIn("SAMLResponse", form_data)
        self.assertNotIn("RelayState", form_data)

    def test_provider_not_found(self):
        """Test returns False when provider doesn't exist"""
        result = send_saml_logout_response(
            provider_pk=99999,  # Non-existent provider
            sls_url="https://sp.example.com/sls",
            logout_request_id="test-request-id",
            relay_state=None,
        )

        self.assertFalse(result)

    @patch("authentik.providers.saml.tasks.Event")
    @patch("authentik.providers.saml.tasks.requests.post")
    def test_http_error_creates_event(self, mock_post, mock_event_class):
        """Test HTTP error creates an error event"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        mock_event = MagicMock()
        mock_event_class.new.return_value = mock_event

        result = send_saml_logout_response(
            provider_pk=self.provider.pk,
            sls_url=self.provider.sls_url,
            logout_request_id="test-request-id",
            relay_state=None,
        )

        self.assertFalse(result)

        # Verify error event was created
        mock_event_class.new.assert_called_once()
        call_kwargs = mock_event_class.new.call_args[1]
        self.assertIn("Backchannel logout response failed", call_kwargs["message"])
        mock_event.save.assert_called_once()


class TestSendSamlLogoutRequest(TestCase):
    """Tests for send_saml_logout_request task"""

    def setUp(self):
        """Set up test fixtures"""
        self.cert = create_test_cert()
        self.flow = create_test_flow()

        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            acs_url="https://sp.example.com/acs",
            sls_url="https://sp.example.com/sls",
            issuer="https://idp.example.com",
            signing_kp=self.cert,
        )

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_successful_logout_request(self, mock_post):
        """Test successful POST logout request returns True"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = send_saml_logout_request(
            provider_pk=self.provider.pk,
            sls_url=self.provider.sls_url,
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify the POST was made with correct data
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["timeout"], 10)
        self.assertEqual(
            call_kwargs["headers"]["Content-Type"], "application/x-www-form-urlencoded"
        )

        # Verify form data contains SAMLRequest
        form_data = call_kwargs["data"]
        self.assertIn("SAMLRequest", form_data)

    def test_provider_not_found(self):
        """Test returns False when provider doesn't exist"""
        result = send_saml_logout_request(
            provider_pk=99999,  # Non-existent provider
            sls_url="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
        )

        self.assertFalse(result)

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_http_error_raises(self, mock_post):
        """Test HTTP error raises exception (no try/catch in send_post_logout_request)"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        with self.assertRaises(HTTPError):
            send_saml_logout_request(
                provider_pk=self.provider.pk,
                sls_url=self.provider.sls_url,
                name_id="test@example.com",
                name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
                session_index="test-session-123",
            )


class TestSendPostLogoutRequest(TestCase):
    """Tests for send_post_logout_request function"""

    def setUp(self):
        """Set up test fixtures"""
        self.cert = create_test_cert()
        self.flow = create_test_flow()

        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            acs_url="https://sp.example.com/acs",
            sls_url="https://sp.example.com/sls",
            issuer="https://idp.example.com",
            signing_kp=self.cert,
        )

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_successful_post(self, mock_post):
        """Test successful POST returns True"""
        from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination=self.provider.sls_url,
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
        )

        result = send_post_logout_request(self.provider, processor)

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_with_relay_state(self, mock_post):
        """Test POST includes RelayState when present"""
        from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination=self.provider.sls_url,
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state="https://sp.example.com/return",
        )

        result = send_post_logout_request(self.provider, processor)

        self.assertTrue(result)

        # Verify RelayState is included
        form_data = mock_post.call_args[1]["data"]
        self.assertIn("RelayState", form_data)
        self.assertEqual(form_data["RelayState"], "https://sp.example.com/return")

    @patch("authentik.providers.saml.tasks.requests.post")
    def test_connection_error_raises(self, mock_post):
        """Test connection error raises exception"""
        from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor

        mock_post.side_effect = ConnectionError("Connection refused")

        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination=self.provider.sls_url,
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
        )

        with self.assertRaises(ConnectionError):
            send_post_logout_request(self.provider, processor)
