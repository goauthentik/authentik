"""Test blueprints v1 JSON"""
from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import JSONStringImporter
from authentik.core.tests.utils import create_test_flow
from authentik.lib.tests.utils import load_fixture


class TestBlueprintsV1JSON(TransactionTestCase):
    """Test Blueprints"""

    def test_import(self):
        """Test JSON Import"""
        test_flow = create_test_flow()
        importer = JSONStringImporter(
            load_fixture("fixtures/test.json"),
            {
                "flow": str(test_flow.pk),
            },
        )
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
