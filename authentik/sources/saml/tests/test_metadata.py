"""SAML Source tests"""
from defusedxml import ElementTree
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.xml import lxml_from_string
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata import MetadataProcessor


class TestMetadataProcessor(TestCase):
    """Test MetadataProcessor"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_metadata_schema(self):
        """Test Metadata generation being valid"""
        source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            signing_kp=create_test_cert(),
            pre_authentication_flow=create_test_flow(),
        )
        request = self.factory.get("/")
        xml = MetadataProcessor(source, request).build_entity_descriptor()
        metadata = lxml_from_string(xml)

        schema = etree.XMLSchema(etree.parse("xml/saml-schema-metadata-2.0.xsd"))  # nosec
        self.assertTrue(schema.validate(metadata))

    def test_metadata_consistent(self):
        """Test Metadata generation being consistent (xml stays the same)"""
        source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            signing_kp=create_test_cert(),
            pre_authentication_flow=create_test_flow(),
        )
        request = self.factory.get("/")
        xml_a = MetadataProcessor(source, request).build_entity_descriptor()
        xml_b = MetadataProcessor(source, request).build_entity_descriptor()
        self.assertEqual(xml_a, xml_b)

    def test_metadata(self):
        """Test Metadata generation being valid"""
        source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            signing_kp=create_test_cert(),
            pre_authentication_flow=create_test_flow(),
        )
        request = self.factory.get("/")
        xml = MetadataProcessor(source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "authentik")

    def test_metadata_without_signautre(self):
        """Test Metadata generation being valid"""
        source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            pre_authentication_flow=create_test_flow(),
        )
        request = self.factory.get("/")
        xml = MetadataProcessor(source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "authentik")
