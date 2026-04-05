"""Integration tests for SAML Logout - Testing processor and parser together"""

from urllib.parse import parse_qs, urlparse

from django.test import TestCase

from authentik.common.saml.constants import (
    RSA_SHA256,
    SAML_NAME_ID_FORMAT_EMAIL,
)
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.processors.logout_request_parser import LogoutRequestParser


class TestLogoutIntegration(TestCase):
    """Integration tests for SAML Logout - processor and parser working together"""

    def setUp(self):
        """Set up test fixtures"""
        self.flow = create_test_flow()
        self.keypair = create_test_cert()

        # Create provider
        self.provider = SAMLProvider.objects.create(
            name="test-provider",
            authorization_flow=self.flow,
            acs_url="https://sp.example.com/acs",
            sls_url="https://sp.example.com/sls",
            issuer="https://idp.example.com",
            sp_binding="redirect",
            sls_binding="redirect",
            signature_algorithm=RSA_SHA256,
        )

        # Create processor
        self.processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state="https://idp.example.com/flow/return",
        )

        # Create parser for validation
        self.parser = LogoutRequestParser(self.provider)

    def test_post_binding_roundtrip(self):
        """Test that a POST-encoded request can be parsed correctly"""
        # Generate the request
        encoded = self.processor.encode_post()

        # Parse it back
        parsed = self.parser.parse(encoded)

        # Verify all fields match
        self.assertEqual(parsed.issuer, self.provider.issuer)
        self.assertEqual(parsed.name_id, "test@example.com")
        self.assertEqual(parsed.name_id_format, SAML_NAME_ID_FORMAT_EMAIL)
        self.assertEqual(parsed.session_index, "test-session-123")
        self.assertIsNotNone(parsed.id)

    def test_redirect_binding_roundtrip(self):
        """Test that a redirect-encoded request can be parsed correctly"""
        # Generate the request
        encoded = self.processor.encode_redirect()

        # Parse it back using detached method
        parsed = self.parser.parse_detached(encoded)

        # Verify all fields match
        self.assertEqual(parsed.issuer, self.provider.issuer)
        self.assertEqual(parsed.name_id, "test@example.com")
        self.assertEqual(parsed.name_id_format, SAML_NAME_ID_FORMAT_EMAIL)
        self.assertEqual(parsed.session_index, "test-session-123")
        self.assertIsNotNone(parsed.id)

    def test_signed_post_binding_roundtrip(self):
        """Test that a signed POST request can be parsed and verified"""
        # Enable signing
        self.provider.signing_kp = self.keypair
        self.provider.sign_logout_request = True
        self.provider.save()

        # Create new processor with signing
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="signed@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="signed-session-456",
            relay_state="https://idp.example.com/flow/signed",
        )

        # Generate signed request
        encoded = processor.encode_post()

        # Create parser with verification enabled
        parser = LogoutRequestParser(self.provider)

        # Parse it - this would validate signature if verification is enabled
        parsed = parser.parse(encoded)

        # Verify all fields match
        self.assertEqual(parsed.issuer, self.provider.issuer)
        self.assertEqual(parsed.name_id, "signed@example.com")
        self.assertEqual(parsed.name_id_format, SAML_NAME_ID_FORMAT_EMAIL)
        self.assertEqual(parsed.session_index, "signed-session-456")

    def test_redirect_url_can_be_parsed(self):
        """Test that the redirect URL contains parseable parameters"""
        # Generate redirect URL
        url = self.processor.get_redirect_url()

        # Parse URL and extract SAMLRequest
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        # Parse the SAMLRequest
        saml_request = params["SAMLRequest"][0]
        parsed = self.parser.parse_detached(saml_request)

        # Verify parsing succeeded
        self.assertEqual(parsed.issuer, self.provider.issuer)
        self.assertEqual(parsed.name_id, "test@example.com")
        self.assertEqual(parsed.name_id_format, SAML_NAME_ID_FORMAT_EMAIL)

    def test_signed_redirect_url_parameters(self):
        """Test that signed redirect URL has all required parameters for validation"""
        # Enable signing
        self.provider.signing_kp = self.keypair
        self.provider.sign_logout_request = True
        self.provider.save()

        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session",
            relay_state="https://idp.example.com/return",
        )

        # Generate signed redirect URL
        url = processor.get_redirect_url()

        # Parse URL
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        # Verify all required parameters are present
        self.assertIn("SAMLRequest", params)
        self.assertIn("RelayState", params)
        self.assertIn("SigAlg", params)
        self.assertIn("Signature", params)

        # Verify signature algorithm matches provider configuration
        self.assertEqual(params["SigAlg"][0], RSA_SHA256)

        # Parse the SAMLRequest (unsigned XML)
        parsed = self.parser.parse_detached(params["SAMLRequest"][0])
        self.assertEqual(parsed.issuer, self.provider.issuer)

    def test_form_data_can_be_parsed(self):
        """Test that form data generates parseable POST request"""
        # Get form data
        form_data = self.processor.get_post_form_data()

        # Parse the SAMLRequest from form data
        parsed = self.parser.parse(form_data["SAMLRequest"])

        # Verify parsing succeeded
        self.assertEqual(parsed.issuer, self.provider.issuer)
        self.assertEqual(parsed.name_id, "test@example.com")
        self.assertEqual(parsed.name_id_format, SAML_NAME_ID_FORMAT_EMAIL)
        self.assertEqual(parsed.session_index, "test-session-123")

    def test_processor_without_optional_fields(self):
        """Test integration when optional fields are missing"""
        # Create processor without session_index and relay_state
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="minimal@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index=None,
            relay_state=None,
        )

        # Test POST binding
        encoded_post = processor.encode_post()
        parsed_post = self.parser.parse(encoded_post)
        self.assertEqual(parsed_post.name_id, "minimal@example.com")
        self.assertIsNone(parsed_post.session_index)

        # Test redirect binding
        encoded_redirect = processor.encode_redirect()
        parsed_redirect = self.parser.parse_detached(encoded_redirect)
        self.assertEqual(parsed_redirect.name_id, "minimal@example.com")
        self.assertIsNone(parsed_redirect.session_index)

    def test_multiple_processors_same_provider(self):
        """Test that multiple processors can use the same provider"""
        # Create multiple processors with different data
        processor1 = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp1.example.com/sls",
            name_id="user1@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="session-1",
            relay_state="https://idp.example.com/flow1",
        )

        processor2 = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp2.example.com/sls",
            name_id="user2@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="session-2",
            relay_state="https://idp.example.com/flow2",
        )

        # Generate requests
        encoded1 = processor1.encode_post()
        encoded2 = processor2.encode_post()

        # Parse both with same parser
        parsed1 = self.parser.parse(encoded1)
        parsed2 = self.parser.parse(encoded2)

        # Verify they have different data
        self.assertEqual(parsed1.name_id, "user1@example.com")
        self.assertEqual(parsed2.name_id, "user2@example.com")
        self.assertEqual(parsed1.session_index, "session-1")
        self.assertEqual(parsed2.session_index, "session-2")

        # But same issuer
        self.assertEqual(parsed1.issuer, parsed2.issuer)
        self.assertEqual(parsed1.issuer, self.provider.issuer)
