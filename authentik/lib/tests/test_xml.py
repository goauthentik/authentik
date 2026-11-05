"""Test XML utilities"""

from django.test import SimpleTestCase
from lxml.etree import XMLSyntaxError  # nosec

from authentik.lib.xml import UnsafeXML, lxml_from_string


class TestXML(SimpleTestCase):
    """Test XML utilities"""

    def test_parse(self):
        """Test that a document without a document type declaration is parsed"""
        root = lxml_from_string(
            '<?xml version="1.0"?>'
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
        )

        self.assertEqual(root.tag, "{urn:oasis:names:tc:SAML:2.0:protocol}AuthnRequest")

    def test_doctype(self):
        """Test that a document type declaration is refused"""
        with self.assertRaisesMessage(UnsafeXML, "XML document contains a DOCTYPE declaration"):
            lxml_from_string(
                '<?xml version="1.0"?>'
                "<!DOCTYPE samlp:AuthnRequest>"
                '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
                'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
            )

    def test_doctype_utf16(self):
        """Test that a document type declaration is refused in a UTF-16 document"""
        document = (
            '<?xml version="1.0" encoding="UTF-16"?>'
            "<!DOCTYPE samlp:AuthnRequest>"
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
        ).encode("utf-16")

        with self.assertRaisesMessage(UnsafeXML, "XML document contains a DOCTYPE declaration"):
            lxml_from_string(document)

    def test_doctype_internal_subset(self):
        """Test that a document type declaration with an internal subset is refused"""
        with self.assertRaisesMessage(UnsafeXML, "XML document contains a DOCTYPE declaration"):
            lxml_from_string('<?xml version="1.0"?><!DOCTYPE d [<!ENTITY g "h">]><d>&g;</d>')

    def test_doctype_external_identifier(self):
        """Test that a document type declaration with an external identifier is refused"""
        with self.assertRaisesMessage(UnsafeXML, "XML document contains a DOCTYPE declaration"):
            lxml_from_string(
                '<?xml version="1.0"?>'
                '<!DOCTYPE d SYSTEM "https://sp.example.invalid/d.dtd">'
                "<d/>"
            )

    def test_declared_encoding_mismatch(self):
        """Test that a document whose declared encoding does not match its content is refused"""
        document = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<!DOCTYPE samlp:AuthnRequest>"
            '<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2026-05-19T01:01:53.461Z"/>'
        ).encode("utf-16")

        with self.assertRaisesMessage(UnsafeXML, "XML document could not be validated"):
            lxml_from_string(document)

    def test_declared_encoding_unsupported(self):
        """Test that a document in an encoding that cannot be validated is refused"""
        document = '<?xml version="1.0" encoding="UTF-32"?><!DOCTYPE d><d>x</d>'.encode("utf-32")

        with self.assertRaisesMessage(UnsafeXML, "XML document could not be validated"):
            lxml_from_string(document)

    def test_doctype_in_comment(self):
        """Test that the text of a document type declaration in a comment is not one"""
        root = lxml_from_string('<?xml version="1.0"?><!-- <!DOCTYPE d> --><d/>')

        self.assertEqual(root.tag, "d")

    def test_doctype_in_attribute(self):
        """Test that the text of a document type declaration in an attribute is not one"""
        root = lxml_from_string('<?xml version="1.0"?><d a="&lt;!DOCTYPE d&gt;"/>')

        self.assertEqual(root.attrib["a"], "<!DOCTYPE d>")

    def test_single_byte_encoding(self):
        """Test that a document in a single-byte encoding is parsed"""
        document = '<?xml version="1.0" encoding="windows-1252"?><d>caf\xe9</d>'.encode("cp1252")

        root = lxml_from_string(document)

        self.assertEqual(root.text, "caf\xe9")

    def test_nesting_depth(self):
        """Test that the parser keeps the default limit on nesting depth"""
        with self.assertRaises(XMLSyntaxError):
            lxml_from_string("<a>" * 300 + "x" + "</a>" * 300)
