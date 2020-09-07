"""SAML Source tests"""
from defusedxml import ElementTree
from django.test import RequestFactory, TestCase

from passbook.crypto.models import CertificateKeyPair
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.processors.metadata import MetadataProcessor


class TestMetadataProcessor(TestCase):
    """Test MetadataProcessor"""

    def setUp(self):
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="passbook",
            signing_kp=CertificateKeyPair.objects.first(),
        )
        self.factory = RequestFactory()

    def test_metadata(self):
        """Test Metadata generation being valid"""
        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "passbook")
