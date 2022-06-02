"""Test Requests and Responses against schema"""
from base64 import b64encode

from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.tests.utils import get_request
from authentik.lib.xml import lxml_from_string
from authentik.managed.manager import ObjectManager
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.request_parser import AuthNRequestParser
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor


class TestSchema(TestCase):
    """Test Requests and Responses against schema"""

    def setUp(self):
        ObjectManager().run()
        cert = create_test_cert()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=create_test_flow(),
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
            pre_authentication_flow=create_test_flow(),
        )
        self.factory = RequestFactory()

    def test_request_schema(self):
        """Test generated AuthNRequest against Schema"""
        http_request = get_request("/")

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        metadata = lxml_from_string(request)

        schema = etree.XMLSchema(etree.parse("xml/saml-schema-protocol-2.0.xsd"))  # nosec
        self.assertTrue(schema.validate(metadata))

    def test_response_schema(self):
        """Test generated AuthNRequest against Schema"""
        http_request = get_request("/")

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

        metadata = lxml_from_string(response)

        schema = etree.XMLSchema(etree.parse("xml/saml-schema-protocol-2.0.xsd"))
        self.assertTrue(schema.validate(metadata))
