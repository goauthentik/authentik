"""Test blueprints v1"""

from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Application
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1MetaClean(TransactionTestCase):
    """Test Blueprints meta clean model"""

    def test_meta_clean(self):
        """Test meta clean"""

        num_apps = 5

        for _ in range(num_apps):
            Application.objects.create(name=generate_id(), slug=generate_id())

        all_apps = Application.objects.all()

        # Ensure all objects exist
        self.assertEqual(len(all_apps), num_apps)

        import_yaml = load_fixture("fixtures/meta_clean.yaml")

        importer = Importer.from_string(import_yaml)
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

        all_apps = Application.objects.all()

        # Ensure all objects removed
        self.assertEqual(len(all_apps), 0)
