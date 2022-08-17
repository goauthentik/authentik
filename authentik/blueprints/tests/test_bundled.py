"""test packaged blueprints"""
from pathlib import Path
from typing import Callable

from django.test import TransactionTestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.blueprints.v1.importer import Importer
from authentik.tenants.models import Tenant


class TestBundled(TransactionTestCase):
    """Empty class, test methods are added dynamically"""

    @apply_blueprint("default/90-default-tenant.yaml")
    def test_decorator_static(self):
        """Test @apply_blueprint decorator"""
        self.assertTrue(Tenant.objects.filter(domain="authentik-default").exists())


def blueprint_tester(file_name: str) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestBundled):
        with open(file_name, "r", encoding="utf8") as blueprint:
            importer = Importer(blueprint.read())
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

    return tester


for blueprint_file in Path("blueprints/").glob("**/*.yaml"):
    setattr(TestBundled, f"test_blueprint_{blueprint_file}", blueprint_tester(blueprint_file))
