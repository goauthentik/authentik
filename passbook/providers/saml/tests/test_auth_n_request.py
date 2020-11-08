"""Test AuthN Request generator and parser"""
from django.contrib.sessions.middleware import SessionMiddleware
from django.http.request import HttpRequest, QueryDict
from django.test import RequestFactory, TestCase
from guardian.utils import get_anonymous_user

from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow
from passbook.providers.saml.models import SAMLProvider
from passbook.providers.saml.processors.assertion import AssertionProcessor
from passbook.providers.saml.processors.request_parser import AuthNRequestParser
from passbook.providers.saml.utils.encoding import deflate_and_base64_encode
from passbook.sources.saml.exceptions import MismatchedRequestID
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.processors.request import (
    SESSION_REQUEST_ID,
    RequestProcessor,
)
from passbook.sources.saml.processors.response import ResponseProcessor


def dummy_get_response(request: HttpRequest):  # pragma: no cover
    """Dummy get_response for SessionMiddleware"""
    return None


class TestAuthNRequest(TestCase):
    """Test AuthN Request generator and parser"""

    def setUp(self):
        self.provider = SAMLProvider.objects.create(
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=CertificateKeyPair.objects.first(),
            verification_kp=CertificateKeyPair.objects.first(),
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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(http_request)
        http_request.session.save()

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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(http_request)
        http_request.session.save()

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        params = request_proc.build_auth_n_detached()
        # Now we check the ID and signature
        parsed_request = AuthNRequestParser(self.provider).parse_detached(
            params["SAMLRequest"], "test_state", params["Signature"], params["SigAlg"]
        )
        self.assertEqual(parsed_request.id, request_proc.request_id)
        self.assertEqual(parsed_request.relay_state, "test_state")

    def test_request_id_invalid(self):
        """Test generated AuthNRequest with invalid request ID"""
        http_request = self.factory.get("/")
        http_request.user = get_anonymous_user()

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(http_request)
        http_request.session.save()

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        # change the request ID
        http_request.session[SESSION_REQUEST_ID] = "test"
        http_request.session.save()

        # To get an assertion we need a parsed request (parsed by provider)
        parsed_request = AuthNRequestParser(self.provider).parse(
            deflate_and_base64_encode(request), "test_state"
        )
        # Now create a response and convert it to string (provider)
        response_proc = AssertionProcessor(self.provider, http_request, parsed_request)
        response = response_proc.build_response()

        # Now parse the response (source)
        http_request.POST = QueryDict(mutable=True)
        http_request.POST["SAMLResponse"] = deflate_and_base64_encode(response)

        response_parser = ResponseProcessor(self.source)

        with self.assertRaises(MismatchedRequestID):
            response_parser.parse(http_request)
