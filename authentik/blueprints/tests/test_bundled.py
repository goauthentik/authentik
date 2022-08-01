"""test packaged blueprints"""
from glob import glob
from pathlib import Path
from typing import Callable

from django.test import TransactionTestCase
from django.utils.text import slugify

from authentik.blueprints.v1.importer import Importer


class TestBundled(TransactionTestCase):
    """Empty class, test methods are added dynamically"""


def blueprint_tester(file_name: str) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestBundled):
        with open(file_name, "r", encoding="utf8") as flow_yaml:
            importer = Importer(flow_yaml.read())
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())

    return tester


for flow_file in glob("blueprints/**/*.yaml", recursive=True):
    method_name = slugify(Path(flow_file).stem).replace("-", "_").replace(".", "_")
    setattr(TestBundled, f"test_flow_{method_name}", blueprint_tester(flow_file))
