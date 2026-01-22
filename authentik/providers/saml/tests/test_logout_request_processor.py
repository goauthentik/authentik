"""Test LogoutRequestProcessor - Unit Tests"""

import base64
import zlib
from urllib.parse import parse_qs, urlparse

from django.test import TestCase
from lxml import etree

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    RSA_SHA256,
    SAML_NAME_ID_FORMAT_EMAIL,
)


class TestLogoutRequestProcessor(TestCase):
    """Unit tests for LogoutRequestProcessor - no external dependencies"""

    def setUp(self):
        """Set up test fixtures"""
        self.flow = create_test_flow()

        # Create a signing keypair
        self.keypair = create_test_cert()

        # Create provider without signing first
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

    def test_build_creates_valid_logout_request_xml(self):
        """Test that build() creates valid LogoutRequest XML"""
        logout_request = self.processor.build()

        # Check it's an Element
        self.assertIsNotNone(logout_request)
        self.assertEqual(logout_request.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutRequest")

        # Check required attributes
        self.assertIn("ID", logout_request.attrib)
        self.assertIn("Version", logout_request.attrib)
        self.assertEqual(logout_request.attrib["Version"], "2.0")
        self.assertIn("IssueInstant", logout_request.attrib)
        self.assertEqual(logout_request.attrib["Destination"], "https://sp.example.com/sls")

        # Check Issuer element
        issuer = logout_request.find(f"{{{NS_SAML_ASSERTION}}}Issuer", NS_MAP)
        self.assertIsNotNone(issuer)
        self.assertEqual(issuer.text, "https://idp.example.com")

        # Check NameID element
        name_id = logout_request.find(f"{{{NS_SAML_ASSERTION}}}NameID", NS_MAP)
        self.assertIsNotNone(name_id)
        self.assertEqual(name_id.text, "test@example.com")
        self.assertEqual(name_id.attrib["Format"], SAML_NAME_ID_FORMAT_EMAIL)

        # Check SessionIndex element
        session_index = logout_request.find(f"{{{NS_SAML_PROTOCOL}}}SessionIndex", NS_MAP)
        self.assertIsNotNone(session_index)
        self.assertEqual(session_index.text, "test-session-123")

    def test_encode_post_without_signing(self):
        """Test encode_post() without signing"""
        # Provider has no signing_kp, so it shouldn't sign
        encoded = self.processor.encode_post()

        # Should be base64 encoded
        self.assertIsInstance(encoded, str)

        # Decode and check it's valid XML
        decoded_xml = base64.b64decode(encoded)
        root = etree.fromstring(decoded_xml)

        # Verify root element
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutRequest")

        # Should not have a Signature element
        signature = root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        self.assertIsNone(signature)

        # Verify content matches what we set
        issuer = root.find(f"{{{NS_SAML_ASSERTION}}}Issuer", NS_MAP)
        self.assertEqual(issuer.text, "https://idp.example.com")

        name_id = root.find(f"{{{NS_SAML_ASSERTION}}}NameID", NS_MAP)
        self.assertEqual(name_id.text, "test@example.com")

    def test_encode_post_with_signing(self):
        """Test encode_post() with signing enabled"""
        # Enable signing
        self.provider.signing_kp = self.keypair
        self.provider.sign_logout_request = True
        self.provider.save()

        # Create new processor with signing provider
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state="https://idp.example.com/flow/return",
        )

        encoded = processor.encode_post()

        # Decode and check it has a signature
        decoded_xml = base64.b64decode(encoded)
        root = etree.fromstring(decoded_xml)

        # Should have a Signature element
        signature = root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        self.assertIsNotNone(signature)

        # Check signature is after Issuer element (SAML spec requirement)
        issuer = root.find(f"{{{NS_SAML_ASSERTION}}}Issuer", NS_MAP)
        issuer_index = list(root).index(issuer)
        sig_index = list(root).index(signature)
        self.assertGreater(sig_index, issuer_index)

    def test_encode_redirect_creates_deflated_encoded_request(self):
        """Test encode_redirect() creates properly deflated and encoded request"""
        encoded = self.processor.encode_redirect()

        # Should be base64 encoded string
        self.assertIsInstance(encoded, str)

        # Try to decode
        decoded = base64.b64decode(encoded)
        # -15 for raw deflate
        inflated = zlib.decompress(decoded, -15)

        # Should be valid XML with declaration
        self.assertTrue(inflated.startswith(b"<?xml"))

        # Parse the XML
        root = etree.fromstring(inflated)
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutRequest")

        # Verify it has the expected content
        issuer = root.find(f"{{{NS_SAML_ASSERTION}}}Issuer", NS_MAP)
        self.assertEqual(issuer.text, "https://idp.example.com")

        name_id = root.find(f"{{{NS_SAML_ASSERTION}}}NameID", NS_MAP)
        self.assertEqual(name_id.text, "test@example.com")

    def test_get_redirect_url_without_signing(self):
        """Test get_redirect_url() without signing"""
        url = self.processor.get_redirect_url()

        # Parse the URL
        parsed_url = urlparse(url)
        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.netloc, "sp.example.com")
        self.assertEqual(parsed_url.path, "/sls")

        # Parse query parameters
        params = parse_qs(parsed_url.query)

        # Should have SAMLRequest and RelayState
        self.assertIn("SAMLRequest", params)
        self.assertIn("RelayState", params)

        # Should NOT have signature parameters
        self.assertNotIn("SigAlg", params)
        self.assertNotIn("Signature", params)

        # RelayState should match
        self.assertEqual(params["RelayState"][0], "https://idp.example.com/flow/return")

        # Verify SAMLRequest is properly encoded
        saml_request = params["SAMLRequest"][0]
        # Should be able to decode it
        decoded = base64.b64decode(saml_request)
        inflated = zlib.decompress(decoded, -15)
        root = etree.fromstring(inflated)
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutRequest")

    def test_get_redirect_url_with_signing(self):
        """Test get_redirect_url() with signing enabled"""
        # Enable signing
        self.provider.signing_kp = self.keypair
        self.provider.sign_logout_request = True
        self.provider.save()

        # Create new processor with signing provider
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state="https://idp.example.com/flow/return",
        )

        url = processor.get_redirect_url()

        # Parse the URL
        parsed_url = urlparse(url)

        # Check the raw query string order - Signature should be last
        query_string = parsed_url.query
        query_parts = query_string.split("&")

        # Verify Signature parameter comes last
        self.assertTrue(
            query_parts[-1].startswith("Signature="),
            f"Signature should be last parameter, got: {query_parts[-1]}",
        )

        # Verify order of signed parameters (everything except Signature)
        signed_params = "&".join(query_parts[:-1])
        # Should be SAMLRequest, RelayState, then SigAlg
        self.assertTrue(signed_params.startswith("SAMLRequest="))
        self.assertIn("&RelayState=", signed_params)
        self.assertIn("&SigAlg=", signed_params)

        # Verify correct order: SAMLRequest comes before RelayState, RelayState before SigAlg
        saml_index = signed_params.index("SAMLRequest=")
        relay_index = signed_params.index("&RelayState=")
        sigalg_index = signed_params.index("&SigAlg=")
        self.assertLess(saml_index, relay_index, "SAMLRequest should come before RelayState")
        self.assertLess(relay_index, sigalg_index, "RelayState should come before SigAlg")

        # Parse for detailed checks
        params = parse_qs(parsed_url.query)

        # Should have exactly these parameters
        self.assertEqual(set(params.keys()), {"SAMLRequest", "RelayState", "SigAlg", "Signature"})

        # Check signature algorithm
        self.assertEqual(params["SigAlg"][0], RSA_SHA256)

        # RelayState should match
        self.assertEqual(params["RelayState"][0], "https://idp.example.com/flow/return")

        # Signature should be base64 encoded
        signature = params["Signature"][0]
        try:
            decoded_sig = base64.b64decode(signature)
            self.assertIsNotNone(decoded_sig)
            self.assertGreater(len(decoded_sig), 0)
        except ValueError, TypeError:
            self.fail("Signature is not valid base64")

    def test_signature_parameter_ordering(self):
        """Test that signature is computed with correct parameter ordering"""
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
            session_index="test-session-123",
            relay_state="test-relay-state",
        )

        # Build the signable query string
        params = {
            "SAMLRequest": processor.encode_redirect(),
            "RelayState": "test-relay-state",
            "SigAlg": RSA_SHA256,
        }

        query_string = processor._build_signable_query_string(params)

        # Check order is correct (SAMLRequest, RelayState, SigAlg)
        parts = query_string.split("&")
        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[0].startswith("SAMLRequest="))
        self.assertTrue(parts[1].startswith("RelayState="))
        self.assertTrue(parts[2].startswith("SigAlg="))

    def test_url_encoding_in_signatures(self):
        """Test that URL encoding is handled correctly in signatures"""
        # Enable signing
        self.provider.signing_kp = self.keypair
        self.provider.sign_logout_request = True
        self.provider.save()

        # Use a relay state with special characters that need encoding
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state="https://idp.example.com/flow?param=value&other=test+space",
        )

        url = processor.get_redirect_url()

        # Parse the URL
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        # RelayState should be properly encoded in URL
        self.assertIn("RelayState", params)
        # parse_qs decodes it, so we should get the original value
        self.assertEqual(
            params["RelayState"][0], "https://idp.example.com/flow?param=value&other=test+space"
        )

        # Should have signature
        self.assertIn("Signature", params)

    def test_get_post_form_data(self):
        """Test get_post_form_data() returns correct form fields"""
        form_data = self.processor.get_post_form_data()

        # Should have SAMLRequest and RelayState
        self.assertIn("SAMLRequest", form_data)
        self.assertIn("RelayState", form_data)

        # SAMLRequest should be base64 encoded
        self.assertIsInstance(form_data["SAMLRequest"], str)
        decoded = base64.b64decode(form_data["SAMLRequest"])
        root = etree.fromstring(decoded)
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutRequest")

        # RelayState should match
        self.assertEqual(form_data["RelayState"], "https://idp.example.com/flow/return")

    def test_processor_without_session_index(self):
        """Test processor works without session_index"""
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index=None,  # No session index
            relay_state="https://idp.example.com/flow/return",
        )

        logout_request = processor.build()

        # Should not have SessionIndex element
        session_index = logout_request.find(f"{{{NS_SAML_PROTOCOL}}}SessionIndex", NS_MAP)
        self.assertIsNone(session_index)

        # Should still have other required elements
        self.assertIsNotNone(logout_request.find(f"{{{NS_SAML_ASSERTION}}}Issuer", NS_MAP))
        self.assertIsNotNone(logout_request.find(f"{{{NS_SAML_ASSERTION}}}NameID", NS_MAP))

    def test_processor_without_relay_state(self):
        """Test processor works without relay_state"""
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state=None,  # No relay state
        )

        url = processor.get_redirect_url()

        # Parse the URL
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

        # Should have SAMLRequest but no RelayState
        self.assertIn("SAMLRequest", params)
        self.assertNotIn("RelayState", params)

        # Form data should have empty RelayState
        form_data = processor.get_post_form_data()
        self.assertEqual(form_data["RelayState"], "")

    def test_signed_redirect_url_without_relay_state(self):
        """Test signed redirect URL without RelayState - signature must be computed correctly"""
        # Enable signing
        self.provider.signing_kp = self.keypair
        self.provider.sign_logout_request = True
        self.provider.save()

        # Create processor without relay_state
        processor = LogoutRequestProcessor(
            provider=self.provider,
            user=None,
            destination="https://sp.example.com/sls",
            name_id="test@example.com",
            name_id_format=SAML_NAME_ID_FORMAT_EMAIL,
            session_index="test-session-123",
            relay_state=None,  # No relay state
        )

        url = processor.get_redirect_url()

        # Parse the URL
        parsed_url = urlparse(url)

        # Check the raw query string order - Signature should be last
        query_string = parsed_url.query
        query_parts = query_string.split("&")

        # Verify Signature parameter comes last
        self.assertTrue(
            query_parts[-1].startswith("Signature="),
            f"Signature should be last parameter, got: {query_parts[-1]}",
        )

        # Verify order of signed parameters (everything except Signature)
        signed_params = "&".join(query_parts[:-1])
        # Should be SAMLRequest, then SigAlg (no RelayState)
        self.assertTrue(signed_params.startswith("SAMLRequest="))
        self.assertIn("&SigAlg=", signed_params)
        self.assertNotIn("&RelayState=", signed_params)

        # Parse for detailed checks
        params = parse_qs(parsed_url.query)

        # Should have exactly these parameters
        self.assertEqual(set(params.keys()), {"SAMLRequest", "SigAlg", "Signature"})

        # Verify signature algorithm
        self.assertEqual(params["SigAlg"][0], RSA_SHA256)

        # Build the expected signable string (without RelayState)
        test_params = {
            "SAMLRequest": params["SAMLRequest"][0],
            "SigAlg": params["SigAlg"][0],
        }

        # The signable string should only contain SAMLRequest and SigAlg
        signable_string = processor._build_signable_query_string(test_params)

        # Should only have 2 parts (no RelayState)
        parts = signable_string.split("&")
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[0].startswith("SAMLRequest="))
        self.assertTrue(parts[1].startswith("SigAlg="))

        # Signature should be valid base64
        signature = params["Signature"][0]
        try:
            decoded_sig = base64.b64decode(signature)
            self.assertIsNotNone(decoded_sig)
            self.assertGreater(len(decoded_sig), 0)
        except ValueError, TypeError:
            self.fail("Signature is not valid base64")
