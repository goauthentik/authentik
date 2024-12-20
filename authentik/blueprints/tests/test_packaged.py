"""test packaged blueprints"""

from collections.abc import Callable
from pathlib import Path

from django.test import TransactionTestCase

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.tests import apply_blueprint
from authentik.blueprints.v1.importer import Importer
from authentik.brands.models import Brand


class TestPackaged(TransactionTestCase):
    """Empty class, test methods are added dynamically"""

    @apply_blueprint("default/default-brand.yaml")
    def test_decorator_static(self):
        """Test @apply_blueprint decorator"""
        self.assertTrue(Brand.objects.filter(domain="authentik-default").exists())


def blueprint_tester(file_name: Path) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestPackaged):
        base = Path("blueprints/")
        rel_path = Path(file_name).relative_to(base)
        importer = Importer.from_string(BlueprintInstance(path=str(rel_path)).retrieve())
        validation, logs = importer.validate()
        self.assertTrue(validation, logs)
        self.assertTrue(importer.apply())

    return tester


for blueprint_file in Path("blueprints/").glob("**/*.yaml"):
    if "local" in str(blueprint_file):
        continue
    setattr(TestPackaged, f"test_blueprint_{blueprint_file}", blueprint_tester(blueprint_file))
