"""Test unified SAML endpoint helpers."""

from django.test import SimpleTestCase

from authentik.lib.tests.utils import load_fixture
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.providers.saml.views.unified import (
    SAML_MESSAGE_TYPE_AUTHN_REQUEST,
    SAML_MESSAGE_TYPE_LOGOUT_REQUEST,
    detect_saml_message_type,
)


class TestDetectSAMLMessageType(SimpleTestCase):
    """Test SAML request type detection."""

    def test_redirect_authn_request_with_xml_declaration(self):
        """Detect redirect-binding AuthnRequest with an XML declaration."""
        request = deflate_and_base64_encode(
            load_fixture("fixtures/authn_request_xml_declaration.xml")
        )

        self.assertEqual(
            detect_saml_message_type(request, is_post_binding=False),
            SAML_MESSAGE_TYPE_AUTHN_REQUEST,
        )

    def test_redirect_logout_request_with_xml_declaration(self):
        """Detect redirect-binding LogoutRequest with an XML declaration."""
        request = deflate_and_base64_encode(
            load_fixture("fixtures/logout_request_xml_declaration.xml")
        )

        self.assertEqual(
            detect_saml_message_type(request, is_post_binding=False),
            SAML_MESSAGE_TYPE_LOGOUT_REQUEST,
        )
