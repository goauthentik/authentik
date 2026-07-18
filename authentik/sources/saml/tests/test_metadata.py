"""SAML Source tests"""

from defusedxml import ElementTree
from django.test import RequestFactory, TestCase
from lxml import etree  # nosec

from authentik.common.saml.constants import NS_MAP
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPairRing, CertificateKeyPairRingBinding
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

    def test_metadata_prefers_single_signing_kp_over_signing_ring(self):
        """Test metadata emits only single signing KP when both KP and ring are set."""
        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        ring_kp_a = create_test_cert()
        ring_kp_b = create_test_cert()
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=ring_kp_a, order=0)
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=ring_kp_b, order=1)
        self.source.signing_kp_ring = ring
        self.source.save(update_fields=["signing_kp_ring"])

        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = lxml_from_string(xml)
        certs = metadata.xpath(
            "//md:SPSSODescriptor/md:KeyDescriptor[@use='signing']//ds:X509Certificate/text()",
            namespaces=NS_MAP,
        )
        self.assertEqual(len(certs), 1)

    def test_metadata_uses_ring_entries_when_single_signing_kp_missing(self):
        """Test metadata emits all signing ring entries when single signing KP is unset."""
        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        ring_kp_a = create_test_cert()
        ring_kp_b = create_test_cert()
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=ring_kp_a, order=0)
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=ring_kp_b, order=1)
        self.source.signing_kp = None
        self.source.signing_kp_ring = ring
        self.source.save(update_fields=["signing_kp", "signing_kp_ring"])

        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = lxml_from_string(xml)
        certs = metadata.xpath(
            "//md:SPSSODescriptor/md:KeyDescriptor[@use='signing']//ds:X509Certificate/text()",
            namespaces=NS_MAP,
        )
        self.assertEqual(len(certs), 2)

    def test_metadata_uses_ring_entries_for_encryption(self):
        """Test metadata emits all encryption ring entries when single encryption KP is unset."""
        ring = CertificateKeyPairRing.objects.create(name=generate_id())
        ring_kp_a = create_test_cert()
        ring_kp_b = create_test_cert()
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=ring_kp_a, order=0)
        CertificateKeyPairRingBinding.objects.create(ring=ring, keypair=ring_kp_b, order=1)
        self.source.encryption_kp = None
        self.source.encryption_kp_ring = ring
        self.source.save(update_fields=["encryption_kp", "encryption_kp_ring"])

        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = lxml_from_string(xml)
        certs = metadata.xpath(
            "//md:SPSSODescriptor/md:KeyDescriptor[@use='encryption']//ds:X509Certificate/text()",
            namespaces=NS_MAP,
        )
        self.assertEqual(len(certs), 2)
