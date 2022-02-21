"""logout request tests"""
from django.test import TestCase

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.managed.manager import ObjectManager
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.logout_request_parser import LogoutRequestParser
from authentik.sources.saml.models import SAMLSource

LOGOUT_REQUEST = (
    "lJLNauMwEMdfRejuSJbtEIvYsBAWDNlltyk99DaxJ41AllzNGNq3L3Z7CD0EehJo5vf/ENoTjH6yx/gSZ37A1xmJxdvo"
    "A9ll0sg5BRuBHNkAI5Ll3p5+/Tlas9EWiDCxi0HeINN9ZkqRYx+9FN2hkW7IDEJ+1vllWxfbAvq6wmKAEvKq1PW5HnbY"
    "V6aqy1KKJ0zkYmik2WgpOqIZu0AMgRtptDGZNpnJH01uC2PL7UbvzLMUByR2AXglr8yTVcrHHvw1Ettaa61gmrzr1xW1"
    "VFCMxIp8VAkHl7BnJdv1pezqmsTvmEbg+02XGzdkl3XVYmDH77JdVLJFP6Npr240vwz+wojdQSzH/xm8uzhMjbylpDj9"
    "uzv+eThOEMhhYKnaz1DfvkT7EQAA//8="
)


class TestLogoutRequest(TestCase):
    """Test LogoutRequest generator and parser"""

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
            pre_authentication_flow=create_test_flow(),
            signing_kp=cert,
        )

    def test_static(self):
        """Test static LogoutRequest"""
        request = LogoutRequestParser(self.provider).parse_detached(LOGOUT_REQUEST)
        self.assertEqual(request.id, "id-2ea1b01f69363ac95e3da4a15409b9d8ec525944")
        self.assertIsNone(request.issuer)
