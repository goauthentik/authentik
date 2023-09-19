"""Test blueprints v1"""
from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1State(TransactionTestCase):
    """Test Blueprints state attribute"""

    def test_state_present(self):
        """Test state present"""
        flow_slug = generate_id()
        import_yaml = load_fixture("fixtures/state_present.yaml", id=flow_slug)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure object exists
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.slug, flow_slug)

        # Update object
        flow.title = "bar"
        flow.save()

        flow.refresh_from_db()
        self.assertEqual(flow.title, "bar")

        # Ensure importer updates it
        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.title, "foo")

    def test_state_created(self):
        """Test state created"""
        flow_slug = generate_id()
        import_yaml = load_fixture("fixtures/state_created.yaml", id=flow_slug)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure object exists
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.slug, flow_slug)

        # Update object
        flow.title = "bar"
        flow.save()

        flow.refresh_from_db()
        self.assertEqual(flow.title, "bar")

        # Ensure importer doesn't update it
        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.title, "bar")

    def test_state_absent(self):
        """Test state absent"""
        flow_slug = generate_id()
        import_yaml = load_fixture("fixtures/state_created.yaml", id=flow_slug)

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        # Ensure object exists
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertEqual(flow.slug, flow_slug)

        import_yaml = load_fixture("fixtures/state_absent.yaml", id=flow_slug)
        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        flow: Flow = Flow.objects.filter(slug=flow_slug).first()
        self.assertIsNone(flow)
