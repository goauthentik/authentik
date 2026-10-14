"""Task module import tests"""

from ast import Import, ImportFrom, parse
from pathlib import Path

from django.test import SimpleTestCase

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
# Registry modules that import actors from elsewhere purely so they get registered;
# a lazy import would never run and the actors would go missing.
EAGER_REGISTRIES = {
    PACKAGE_ROOT / "blueprints" / "tasks.py",
    PACKAGE_ROOT / "enterprise" / "lifecycle" / "tasks.py",
}


class TestLazyTaskImports(SimpleTestCase):
    """Every tasks module must only use lazy imports at module level"""

    def test_lazy_imports(self):
        """All module-level imports in tasks.py files are lazy"""
        for path in PACKAGE_ROOT.rglob("tasks.py"):
            if path in EAGER_REGISTRIES:
                continue
            for node in parse(path.read_text()).body:
                if not isinstance(node, Import | ImportFrom):
                    continue
                if isinstance(node, ImportFrom) and node.module == "__future__":
                    continue
                with self.subTest(path=str(path.relative_to(PACKAGE_ROOT)), line=node.lineno):
                    self.assertTrue(node.is_lazy, "import is not lazy")
