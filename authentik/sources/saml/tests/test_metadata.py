"""SAML Source tests"""
from defusedxml import ElementTree
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
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
            signing_kp=CertificateKeyPair.objects.first(),
            pre_authentication_flow=Flow.objects.get(slug="default-source-pre-authentication"),
        )
        request = self.factory.get("/")
        xml = MetadataProcessor(source, request).build_entity_descriptor()
        metadata = etree.fromstring(xml)  # nosec

        schema = etree.XMLSchema(etree.parse("xml/saml-schema-metadata-2.0.xsd"))  # nosec
        self.assertTrue(schema.validate(metadata))

    def test_metadata(self):
        """Test Metadata generation being valid"""
        source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            signing_kp=CertificateKeyPair.objects.first(),
            pre_authentication_flow=Flow.objects.get(slug="default-source-pre-authentication"),
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
            pre_authentication_flow=Flow.objects.get(slug="default-source-pre-authentication"),
        )
        request = self.factory.get("/")
        xml = MetadataProcessor(source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "authentik")
