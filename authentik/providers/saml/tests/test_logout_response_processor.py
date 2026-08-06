"""logout response tests"""

from defusedxml import ElementTree
from django.test import RequestFactory, TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.common.saml.constants import (
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    NS_SIGNATURE,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.logout_request_parser import LogoutRequest
from authentik.providers.saml.processors.logout_response_processor import LogoutResponseProcessor
from authentik.providers.saml.processors.metadata import MetadataProcessor


class TestLogoutResponse(TestCase):
    """Test LogoutResponse processor"""

    @apply_blueprint("system/providers-saml.yaml")
    def setUp(self):
        cert = create_test_cert()
        self.factory = RequestFactory()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=create_test_flow(),
            acs_url="http://testserver/source/saml/provider/acs/",
            sls_url="http://testserver/source/saml/provider/sls/",
            signing_kp=cert,
            verification_kp=cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.provider.save()
        self.application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )

    def test_build_response(self):
        """Test building a LogoutResponse uses the generated issuer from the assertion"""
        # Generate the issuer the same way the assertion/metadata processors would
        request = self.factory.get("/")
        metadata_processor = MetadataProcessor(self.provider, request)
        generated_issuer = metadata_processor._get_issuer_value()

        logout_request = LogoutRequest(
            id="test-request-id",
            issuer="test-sp",
            relay_state="test-relay-state",
        )

        # Pass the generated issuer as if it came from SAMLSession.issuer
        processor = LogoutResponseProcessor(
            self.provider,
            logout_request,
            destination=self.provider.sls_url,
            issuer=generated_issuer,
        )
        response_xml = processor.build_response(status="Success")

        # Parse and verify
        root = ElementTree.fromstring(response_xml)
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutResponse")
        self.assertEqual(root.attrib["Version"], "2.0")
        self.assertEqual(root.attrib["Destination"], self.provider.sls_url)
        self.assertEqual(root.attrib["InResponseTo"], "test-request-id")

        # Check Issuer matches the generated issuer from the assertion processor
        issuer = root.find(f"{{{NS_SAML_ASSERTION}}}Issuer")
        self.assertEqual(issuer.text, generated_issuer)

        # Check Status
        status = root.find(f".//{{{NS_SAML_PROTOCOL}}}StatusCode")
        self.assertEqual(status.attrib["Value"], "urn:oasis:names:tc:SAML:2.0:status:Success")

    def test_build_response_signed(self):
        """Test building a signed LogoutResponse"""
        self.provider.sign_logout_response = True
        self.provider.save()

        logout_request = LogoutRequest(
            id="test-request-id",
            issuer="test-sp",
            relay_state="test-relay-state",
        )

        processor = LogoutResponseProcessor(
            self.provider, logout_request, destination=self.provider.sls_url
        )
        response_xml = processor.build_response(status="Success")

        # Parse and verify signature is present
        root = ElementTree.fromstring(response_xml)
        signature = root.find(f".//{{{NS_SIGNATURE}}}Signature")
        self.assertIsNotNone(signature)

        # Verify signature structure
        signed_info = signature.find(f"{{{NS_SIGNATURE}}}SignedInfo")
        self.assertIsNotNone(signed_info)
        signature_value = signature.find(f"{{{NS_SIGNATURE}}}SignatureValue")
        self.assertIsNotNone(signature_value)
        self.assertIsNotNone(signature_value.text)

    def test_no_inresponseto(self):
        """Test building response without a logout request omits InResponseTo attribute"""
        processor = LogoutResponseProcessor(self.provider, None, destination=self.provider.sls_url)
        response_xml = processor.build_response(status="Success")

        root = ElementTree.fromstring(response_xml)
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutResponse")
        self.assertNotIn("InResponseTo", root.attrib)

    def test_no_destination(self):
        """Test building response without destination"""
        logout_request = LogoutRequest(
            id="test-request-id",
            issuer="test-sp",
        )

        processor = LogoutResponseProcessor(self.provider, logout_request, destination=None)
        response_xml = processor.build_response(status="Success")

        root = ElementTree.fromstring(response_xml)
        self.assertNotIn("Destination", root.attrib)

    def test_relay_state_from_logout_request(self):
        """Test that relay_state is taken from logout_request if not provided"""
        logout_request = LogoutRequest(
            id="test-request-id",
            issuer="test-sp",
            relay_state="request-relay-state",
        )

        processor = LogoutResponseProcessor(
            self.provider, logout_request, destination=self.provider.sls_url
        )
        self.assertEqual(processor.relay_state, "request-relay-state")

    def test_relay_state_override(self):
        """Test that explicit relay_state overrides logout_request relay_state"""
        logout_request = LogoutRequest(
            id="test-request-id",
            issuer="test-sp",
            relay_state="request-relay-state",
        )

        processor = LogoutResponseProcessor(
            self.provider,
            logout_request,
            destination=self.provider.sls_url,
            relay_state="explicit-relay-state",
        )
        self.assertEqual(processor.relay_state, "explicit-relay-state")
