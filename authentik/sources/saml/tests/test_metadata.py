"""SAML Source tests"""

from base64 import b64decode

from cryptography.x509 import load_der_x509_certificate
from defusedxml import ElementTree
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.common.saml.constants import NS_MAP
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.xml import lxml_from_string
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata import MetadataProcessor


class TestMetadataProcessor(TestCase):
    """Test MetadataProcessor"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer_override="authentik",
            signing_kp=create_test_cert(),
            encryption_kp=create_test_cert(),
            pre_authentication_flow=create_test_flow(),
        )

    def test_metadata_schema(self):
        """Test Metadata generation being valid"""
        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = lxml_from_string(xml)

        schema = etree.XMLSchema(
            etree.parse("schemas/saml-schema-metadata-2.0.xsd", parser=etree.XMLParser())  # nosec
        )
        self.assertTrue(schema.validate(metadata))

    def test_metadata_consistent(self):
        """Test Metadata generation being consistent (xml stays the same)"""
        request = self.factory.get("/")
        xml_a = MetadataProcessor(self.source, request).build_entity_descriptor()
        xml_b = MetadataProcessor(self.source, request).build_entity_descriptor()
        self.assertEqual(xml_a, xml_b)

    def test_metadata(self):
        """Test Metadata generation being valid"""
        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "authentik")

    def test_metadata_without_signature(self):
        """Test Metadata generation being valid"""
        self.source.signing_kp = None
        self.source.save()
        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "authentik")

    def test_metadata_certificate_chain(self):
        """Test that only the leaf certificate of a certificate chain is included"""
        intermediate = create_test_cert()
        for keypair in (self.source.signing_kp, self.source.encryption_kp):
            keypair.certificate_data += intermediate.certificate_data
            keypair.save()
        request = self.factory.get("/")
        metadata = lxml_from_string(
            MetadataProcessor(self.source, request).build_entity_descriptor()
        )

        for use, keypair in (
            ("signing", self.source.signing_kp),
            ("encryption", self.source.encryption_kp),
        ):
            certs = metadata.xpath(
                f"/md:EntityDescriptor/md:SPSSODescriptor/md:KeyDescriptor[@use='{use}']"
                "/ds:KeyInfo/ds:X509Data/ds:X509Certificate",
                namespaces=NS_MAP,
            )
            self.assertEqual(len(certs), 1)
            self.assertEqual(
                load_der_x509_certificate(b64decode(certs[0].text, validate=True)),
                keypair.certificate,
            )
