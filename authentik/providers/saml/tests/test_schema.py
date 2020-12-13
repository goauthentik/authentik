"""Test Requests and Responses against schema"""
from base64 import b64encode

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from guardian.utils import get_anonymous_user
from lxml import etree  # nosec

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.request_parser import AuthNRequestParser
from authentik.providers.saml.tests.test_auth_n_request import dummy_get_response
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor


class TestSchema(TestCase):
    """Test Requests and Responses against schema"""

    def setUp(self):
        cert = CertificateKeyPair.objects.first()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=cert,
            verification_kp=cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.provider.save()
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            signing_kp=cert,
        )
        self.factory = RequestFactory()

    def test_request_schema(self):
        """Test generated AuthNRequest against Schema"""
        http_request = self.factory.get("/")

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(http_request)
        http_request.session.save()

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        metadata = etree.fromstring(request)  # nosec

        schema = etree.XMLSchema(
            etree.parse("xml/saml-schema-protocol-2.0.xsd")
        )  # nosec
        self.assertTrue(schema.validate(metadata))

    def test_response_schema(self):
        """Test generated AuthNRequest against Schema"""
        http_request = self.factory.get("/")
        http_request.user = get_anonymous_user()

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(http_request)
        http_request.session.save()

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        # To get an assertion we need a parsed request (parsed by provider)
        parsed_request = AuthNRequestParser(self.provider).parse(
            b64encode(request.encode()).decode(), "test_state"
        )
        # Now create a response and convert it to string (provider)
        response_proc = AssertionProcessor(self.provider, http_request, parsed_request)
        response = response_proc.build_response()

        metadata = etree.fromstring(response)  # nosec

        schema = etree.XMLSchema(etree.parse("xml/saml-schema-protocol-2.0.xsd"))
        self.assertTrue(schema.validate(metadata))
