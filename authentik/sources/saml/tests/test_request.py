"""SAML Source AuthnRequest tests"""

from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor


class TestRequestProcessor(TestCase):
    """Test SAML AuthnRequest generation"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer="authentik",
            sso_url="https://idp.example.com/sso",
            pre_authentication_flow=create_test_flow(),
        )

    def test_force_authn_flag(self):
        """Test that ForceAuthn attribute is set when force_authn is True"""
        self.source.force_authn = True
        self.source.save()

        request = self.factory.get("/")
        request.session = {}

        processor = RequestProcessor(self.source, request, "")
        auth_n = processor.get_auth_n()

        self.assertEqual(auth_n.attrib.get("ForceAuthn"), "true")
