"""SAML Source tests"""
from defusedxml import ElementTree
from django.test import RequestFactory, TestCase

from authentik.crypto.models import CertificateKeyPair
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.metadata import MetadataProcessor


class TestMetadataProcessor(TestCase):
    """Test MetadataProcessor"""

    def setUp(self):
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            signing_kp=CertificateKeyPair.objects.first(),
        )
        self.factory = RequestFactory()

    def test_metadata(self):
        """Test Metadata generation being valid"""
        request = self.factory.get("/")
        xml = MetadataProcessor(self.source, request).build_entity_descriptor()
        metadata = ElementTree.fromstring(xml)
        self.assertEqual(metadata.attrib["entityID"], "authentik")
