"""Test blueprints v1"""
from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1Conditions(TransactionTestCase):
    """Test Blueprints conditions attribute"""

    def test_conditions_fulfilled(self):
        """Test conditions fulfilled"""
        flow_slug1 = generate_id()
        flow_slug2 = generate_id()
        import_yaml = load_fixture(
            "fixtures/conditions_fulfilled.yaml", id1=flow_slug1, id2=flow_slug2
        )

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure objects exist
        flow: Flow = Flow.objects.filter(slug=flow_slug1).first()
        self.assertEqual(flow.slug, flow_slug1)
        flow: Flow = Flow.objects.filter(slug=flow_slug2).first()
        self.assertEqual(flow.slug, flow_slug2)

    def test_conditions_not_fulfilled(self):
        """Test conditions not fulfilled"""
        flow_slug1 = generate_id()
        flow_slug2 = generate_id()
        import_yaml = load_fixture(
            "fixtures/conditions_not_fulfilled.yaml", id1=flow_slug1, id2=flow_slug2
        )

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure objects do not exist
        self.assertFalse(Flow.objects.filter(slug=flow_slug1))
        self.assertFalse(Flow.objects.filter(slug=flow_slug2))
