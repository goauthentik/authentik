"""Test unified SAML endpoint helpers."""

import tracemalloc
from base64 import b64encode

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

    def test_post_authn_request(self):
        """Detect POST-binding AuthnRequest."""
        authn_request = (
            '<?xml version="1.0"?>'
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
        )
        request = b64encode(authn_request.encode()).decode()

        self.assertEqual(
            detect_saml_message_type(request, is_post_binding=True),
            SAML_MESSAGE_TYPE_AUTHN_REQUEST,
        )

    def test_post_authn_request_with_doctype(self):
        """Refuse a POST-binding AuthnRequest with a document type declaration."""
        authn_request = (
            '<?xml version="1.0"?>'
            "<!DOCTYPE samlp:AuthnRequest>"
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
        )
        request = b64encode(authn_request.encode()).decode()

        self.assertIsNone(detect_saml_message_type(request, is_post_binding=True))

    def test_redirect_authn_request_uncompressed(self):
        """Detect a redirect-binding AuthnRequest that is not deflated."""
        authn_request = (
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
        )
        request = b64encode(authn_request.encode()).decode()

        self.assertEqual(
            detect_saml_message_type(request, is_post_binding=False),
            SAML_MESSAGE_TYPE_AUTHN_REQUEST,
        )

    def test_redirect_authn_request_over_size_limit(self):
        """Refuse a redirect-binding AuthnRequest that inflates beyond the size limit."""
        request = deflate_and_base64_encode(
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
            + " " * (32 * 1024 * 1024)
        )

        tracemalloc.start()
        self.addCleanup(tracemalloc.stop)
        message_type = detect_saml_message_type(request, is_post_binding=False)
        _, peak = tracemalloc.get_traced_memory()

        self.assertIsNone(message_type)
        self.assertLess(peak, 32 * 1024 * 1024)
