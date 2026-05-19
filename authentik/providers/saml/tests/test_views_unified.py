"""Test unified SAML endpoint helpers."""

from django.test import SimpleTestCase

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
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<saml2p:AuthnRequest xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1fac8a70c9d2766aed298165ed66dcae" Version="2.0" '
            'IssueInstant="2026-05-19T01:01:53.461Z">'
            '<saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">'
            "https://sp.example.invalid/saml"
            "</saml2:Issuer>"
            "</saml2p:AuthnRequest>"
        )

        self.assertEqual(
            detect_saml_message_type(request, is_post_binding=False),
            SAML_MESSAGE_TYPE_AUTHN_REQUEST,
        )

    def test_redirect_logout_request_with_xml_declaration(self):
        """Detect redirect-binding LogoutRequest with an XML declaration."""
        request = deflate_and_base64_encode(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<saml2p:LogoutRequest xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_logout" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z">'
            '<saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">'
            "https://sp.example.invalid/saml"
            "</saml2:Issuer>"
            "</saml2p:LogoutRequest>"
        )

        self.assertEqual(
            detect_saml_message_type(request, is_post_binding=False),
            SAML_MESSAGE_TYPE_LOGOUT_REQUEST,
        )
