"""test packaged blueprints"""
from pathlib import Path
from typing import Callable

from django.test import TransactionTestCase
from django.utils.text import slugify

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.tests import apply_blueprint
from authentik.blueprints.v1.importer import Importer
from authentik.tenants.models import Tenant


class TestBundled(TransactionTestCase):
    """Empty class, test methods are added dynamically"""

    @apply_blueprint("default/90-default-tenant.yaml")
    def test_decorator_static(self):
        """Test @apply_blueprint decorator"""
        self.assertTrue(Tenant.objects.filter(domain="authentik-default").exists())


def blueprint_tester(file_name: Path) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestBundled):
        base = Path("blueprints/")
        rel_path = Path(file_name).relative_to(base)
        importer = Importer(BlueprintInstance(path=str(rel_path)).retrieve())
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

    return tester


for flow_file in Path("blueprints/").glob("**/*.yaml"):
    method_name = slugify(flow_file.stem).replace("-", "_").replace(".", "_")
    setattr(TestBundled, f"test_flow_{method_name}", blueprint_tester(flow_file))
