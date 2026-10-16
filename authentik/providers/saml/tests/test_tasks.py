"""Tests for SAML provider tasks"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from requests.exceptions import ConnectionError, HTTPError
from requests_mock import Mocker

from authentik.common.saml.constants import SAML_NAME_ID_FORMAT_EMAIL
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.tasks import (
    send_post_logout_request,
    send_saml_logout_request,
    send_saml_logout_response,
    update_saml_provider_metadata,
)


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
            issuer_override="https://idp.example.com",
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
            issuer_override="https://idp.example.com",
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
            issuer="https://idp.example.com",
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
            issuer="https://idp.example.com",
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
                issuer="https://idp.example.com",
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
            issuer_override="https://idp.example.com",
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


class TestUpdateSAMLProviderMetadata(TestCase):
    """Tests for update_saml_provider_metadata task"""

    url = "http://sp.example.com/saml/metadata"

    def setUp(self):
        self.provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            acs_url="https://sp.example.com/old-acs",
            sp_binding=SAMLBindings.REDIRECT,
            metadata_url=self.url,
        )

    @Mocker()
    def test_updates_changed_settings(self, mock: Mocker):
        """Test that settings defined by the metadata are updated"""
        mock.get(self.url, text=load_fixture("fixtures/simple.xml"))
        update_saml_provider_metadata.send(self.provider.pk)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.acs_url, "http://localhost:8080/saml/acs")
        self.assertEqual(self.provider.sp_binding, SAMLBindings.POST)
        self.assertEqual(self.provider.audience, "http://localhost:8080/saml/metadata")

    @Mocker()
    def test_updates_all_providers(self, mock: Mocker):
        """Test that the task updates every provider with a metadata URL when run without
        arguments, and leaves providers without a URL alone"""
        other_url = "http://sp2.example.com/saml/metadata"
        other = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            acs_url="https://sp2.example.com/old-acs",
            metadata_url=other_url,
        )
        plain = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            acs_url="https://sp3.example.com/acs",
        )
        mock.get(self.url, text=load_fixture("fixtures/simple.xml"))
        mock.get(other_url, text=load_fixture("fixtures/simple.xml"))
        update_saml_provider_metadata.send()
        self.provider.refresh_from_db()
        other.refresh_from_db()
        plain.refresh_from_db()
        self.assertEqual(self.provider.acs_url, "http://localhost:8080/saml/acs")
        self.assertEqual(other.acs_url, "http://localhost:8080/saml/acs")
        self.assertEqual(plain.acs_url, "https://sp3.example.com/acs")

    @Mocker()
    def test_unchanged(self, mock: Mocker):
        """Test that an unchanged metadata does not touch the provider"""
        mock.get(self.url, text=load_fixture("fixtures/simple.xml"))
        update_saml_provider_metadata.send(self.provider.pk)
        self.provider.refresh_from_db()
        with patch("authentik.providers.saml.models.SAMLProvider.save") as save:
            update_saml_provider_metadata.send(self.provider.pk)
            save.assert_not_called()

    @Mocker()
    def test_updates_certificate_in_place(self, mock: Mocker):
        """Test that a rotated certificate updates the existing keypair instead of
        creating a new one"""
        old_cert = create_test_cert()
        self.provider.verification_kp = old_cert
        self.provider.save()
        keypair_count = CertificateKeyPair.objects.count()
        mock.get(self.url, text=load_fixture("fixtures/cert.xml"))
        update_saml_provider_metadata.send(self.provider.pk)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.verification_kp.pk, old_cert.pk)
        self.assertEqual(
            self.provider.verification_kp.certificate_data, load_fixture("fixtures/cert.pem")
        )
        self.assertEqual(CertificateKeyPair.objects.count(), keypair_count)

    @Mocker()
    def test_fetch_failure_creates_event(self, mock: Mocker):
        """Test that a failed download leaves the provider untouched and logs an event"""
        mock.get(self.url, status_code=404)
        update_saml_provider_metadata.send(self.provider.pk)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.acs_url, "https://sp.example.com/old-acs")
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_ERROR,
                context__message__icontains="Failed to update SAML provider",
            ).exists()
        )

    @Mocker()
    def test_invalid_metadata_creates_event(self, mock: Mocker):
        """Test that invalid metadata leaves the provider untouched and logs an event"""
        mock.get(self.url, text="<foo></foo>")
        update_saml_provider_metadata.send(self.provider.pk)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.acs_url, "https://sp.example.com/old-acs")
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.CONFIGURATION_ERROR,
                context__message__icontains="Failed to update SAML provider",
            ).exists()
        )
