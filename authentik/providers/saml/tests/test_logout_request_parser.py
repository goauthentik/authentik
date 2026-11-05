"""logout request tests"""

from base64 import b64encode

from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.common.saml.constants import SAML_NAME_ID_FORMAT_TRANSIENT
from authentik.common.saml.exceptions import ERROR_CANNOT_DECODE_REQUEST, CannotHandleAssertion
from authentik.common.saml.parsers.logout_request import LogoutRequestParser
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.sources.saml.models import SAMLSource

GET_LOGOUT_REQUEST = (
    "lJLNauMwEMdfRejuSJbtEIvYsBAWDNlltyk99DaxJ41AllzNGNq3L3Z7CD0EehJo5vf/ENoTjH6yx/gSZ37A1xmJxdvo"
    "A9ll0sg5BRuBHNkAI5Ll3p5+/Tlas9EWiDCxi0HeINN9ZkqRYx+9FN2hkW7IDEJ+1vllWxfbAvq6wmKAEvKq1PW5HnbY"
    "V6aqy1KKJ0zkYmik2WgpOqIZu0AMgRtptDGZNpnJH01uC2PL7UbvzLMUByR2AXglr8yTVcrHHvw1Ettaa61gmrzr1xW1"
    "VFCMxIp8VAkHl7BnJdv1pezqmsTvmEbg+02XGzdkl3XVYmDH77JdVLJFP6Npr240vwz+wojdQSzH/xm8uzhMjbylpDj9"
    "uzv+eThOEMhhYKnaz1DfvkT7EQAA//8="
)
POST_LOGOUT_REQUEST = (
    "PHNhbWxwOkxvZ291dFJlcXVlc3QgeG1sbnM6c2FtbD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmFzc2VydGlvb"
    "iIgeG1sbnM6c2FtbHA9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpwcm90b2NvbCIgSUQ9ImlkLWI4ZjRmZDUxZW"
    "Q0MTA2ZjFlNzgyYjk1ZDUxZDlhZDNmMzg1ZTU4MTYiIFZlcnNpb249IjIuMCIgSXNzdWVJbnN0YW50PSIyMDIyLTAyLTI"
    "xVDIyOjUwOjMzLjk5OVoiIERlc3RpbmF0aW9uPSJodHRwOi8vbG9jYWxob3N0OjkwMDAvYXBwbGljYXRpb24vc2FtbC90"
    "ZXN0L3Nsby9wb3N0LyI+PHNhbWw6SXNzdWVyIEZvcm1hdD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOm5hbWVpZ"
    "C1mb3JtYXQ6ZW50aXR5Ij5zYW1sLXRlc3Qtc3A8L3NhbWw6SXNzdWVyPjxzYW1sOk5hbWVJRCBOYW1lUXVhbGlmaWVyPS"
    "JzYW1sLXRlc3Qtc3AiIFNQTmFtZVF1YWxpZmllcj0ic2FtbC10ZXN0LXNwIiBGb3JtYXQ9InVybjpvYXNpczpuYW1lczp"
    "0YzpTQU1MOjIuMDpuYW1laWQtZm9ybWF0OnRyYW5zaWVudCIvPjwvc2FtbHA6TG9nb3V0UmVxdWVzdD4="
)


class TestLogoutRequest(TestCase):
    """Test LogoutRequest parser"""

    @apply_blueprint("system/providers-saml.yaml")
    def setUp(self):
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
            issuer_override="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=cert,
        )

    def test_static_get(self):
        """Test static LogoutRequest"""
        request = LogoutRequestParser().parse_detached(GET_LOGOUT_REQUEST)
        self.assertEqual(request.id, "id-2ea1b01f69363ac95e3da4a15409b9d8ec525944")
        self.assertEqual(request.issuer, "saml-test-sp")
        # The GET request has an empty NameID element with transient format
        self.assertIsNone(request.name_id)  # Empty NameID element returns None
        self.assertEqual(request.name_id_format, SAML_NAME_ID_FORMAT_TRANSIENT)

    def test_static_post(self):
        """Test static LogoutRequest"""
        request = LogoutRequestParser().parse(POST_LOGOUT_REQUEST)
        self.assertEqual(request.id, "id-b8f4fd51ed4106f1e782b95d51d9ad3f385e5816")
        self.assertEqual(request.issuer, "saml-test-sp")
        # The POST request has an empty NameID element with transient format
        self.assertIsNone(request.name_id)  # Empty NameID element returns None
        self.assertEqual(request.name_id_format, SAML_NAME_ID_FORMAT_TRANSIENT)

    def test_malformed(self):
        """Test that malformed logout requests are rejected with a handled error"""
        missing_id = (
            '<samlp:LogoutRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'Version="2.0" IssueInstant="2022-02-21T22:50:33.999Z"/>'
        )
        parser = LogoutRequestParser()
        for payload in ("this is not xml", missing_id):
            with self.subTest(payload=payload, binding="post"):
                with self.assertRaisesMessage(
                    CannotHandleAssertion, str(ERROR_CANNOT_DECODE_REQUEST)
                ):
                    parser.parse(b64encode(payload.encode()).decode())
            with self.subTest(payload=payload, binding="redirect"):
                with self.assertRaisesMessage(
                    CannotHandleAssertion, str(ERROR_CANNOT_DECODE_REQUEST)
                ):
                    parser.parse_detached(deflate_and_base64_encode(payload))

        for binding, method in (("post", parser.parse), ("redirect", parser.parse_detached)):
            with self.subTest(payload="not base64", binding=binding):
                with self.assertRaisesMessage(
                    CannotHandleAssertion, str(ERROR_CANNOT_DECODE_REQUEST)
                ):
                    method("%%%not-base64%%%", None)
