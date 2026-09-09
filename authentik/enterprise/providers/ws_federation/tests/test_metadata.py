from django.test import TestCase
from lxml import etree  # nosec

from authentik.core.models import Application
from authentik.core.tests.utils import RequestFactory, create_test_flow
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.metadata import MetadataProcessor
from authentik.lib.generators import generate_id
from authentik.lib.xml import lxml_from_string


class TestWSFedMetadata(TestCase):
    def setUp(self):
        self.flow = create_test_flow()
        self.provider = WSFederationProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.factory = RequestFactory()

    def test_metadata_generation(self):
        request = self.factory.get("/")
        metadata_a = MetadataProcessor(self.provider, request).build_entity_descriptor()
        metadata_b = MetadataProcessor(self.provider, request).build_entity_descriptor()
        self.assertEqual(metadata_a, metadata_b)

    def test_schema(self):
        """Test that metadata generation is consistent"""
        request = self.factory.get("/")
        metadata = lxml_from_string(
            MetadataProcessor(self.provider, request).build_entity_descriptor()
        )

        schema = etree.XMLSchema(
            etree.parse(source="schemas/ws-federation.xsd", parser=etree.XMLParser())  # nosec
        )
        self.assertTrue(schema.validate(metadata))
