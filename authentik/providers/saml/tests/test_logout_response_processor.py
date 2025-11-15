"""logout response tests"""

from defusedxml import ElementTree
from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.logout_request_parser import LogoutRequest
from authentik.providers.saml.processors.logout_response_processor import LogoutResponseProcessor
from authentik.sources.saml.processors.constants import NS_SAML_ASSERTION, NS_SAML_PROTOCOL


class TestLogoutResponse(TestCase):
    """Test LogoutResponse processor"""

    @apply_blueprint("system/providers-saml.yaml")
    def setUp(self):
        cert = create_test_cert()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=create_test_flow(),
            acs_url="http://testserver/source/saml/provider/acs/",
            sls_url="http://testserver/source/saml/provider/sls/",
            signing_kp=cert,
            verification_kp=cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.provider.save()

    def test_build_response(self):
        """Test building a LogoutResponse"""
        logout_request = LogoutRequest(
            id="test-request-id",
            issuer="test-sp",
            relay_state="test-relay-state",
        )

        processor = LogoutResponseProcessor(
            self.provider, logout_request, destination=self.provider.sls_url
        )
        response_xml = processor.build_response(status="Success")

        # Parse and verify
        root = ElementTree.fromstring(response_xml)
        self.assertEqual(root.tag, f"{{{NS_SAML_PROTOCOL}}}LogoutResponse")
        self.assertEqual(root.attrib["Version"], "2.0")
        self.assertEqual(root.attrib["Destination"], self.provider.sls_url)
        self.assertEqual(root.attrib["InResponseTo"], "test-request-id")

        # Check Issuer
        issuer = root.find(f"{{{NS_SAML_ASSERTION}}}Issuer")
        self.assertEqual(issuer.text, self.provider.issuer)

        # Check Status
        status = root.find(f".//{{{NS_SAML_PROTOCOL}}}StatusCode")
        self.assertEqual(status.attrib["Value"], "urn:oasis:names:tc:SAML:2.0:status:Success")
