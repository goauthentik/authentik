"""Test AuthN Request generator and parser"""
from django.test import RequestFactory, TestCase

from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow
from passbook.providers.saml.models import SAMLProvider
from passbook.providers.saml.processors.request_parser import AuthNRequestParser
from passbook.providers.saml.utils.encoding import deflate_and_base64_encode
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.processors.request import RequestProcessor


class TestAuthNRequest(TestCase):
    """Test AuthN Request generator and parser"""

    def setUp(self):
        self.provider = SAMLProvider.objects.create(
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=CertificateKeyPair.objects.first(),
        )
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="passbook",
            signing_kp=CertificateKeyPair.objects.first(),
        )
        self.factory = RequestFactory()

    def test_signed_valid(self):
        """Test generated AuthNRequest with valid signature"""
        http_request = self.factory.get("/")
        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()
        # Now we check the ID and signature
        parsed_request = AuthNRequestParser(self.provider).parse(
            deflate_and_base64_encode(request), "test_state"
        )
        self.assertEqual(parsed_request.id, request_proc.request_id)
        self.assertEqual(parsed_request.relay_state, "test_state")

    def test_signed_valid_detached(self):
        """Test generated AuthNRequest with valid signature (detached)"""
        http_request = self.factory.get("/")
        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        params = request_proc.build_auth_n_detached()
        # Now we check the ID and signature
        parsed_request = AuthNRequestParser(self.provider).parse_detached(
            params["SAMLRequest"], "test_state", params["Signature"], params["SigAlg"]
        )
        self.assertEqual(parsed_request.id, request_proc.request_id)
        self.assertEqual(parsed_request.relay_state, "test_state")
