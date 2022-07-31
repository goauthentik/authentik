"""test example flows in docs"""
from glob import glob
from pathlib import Path
from typing import Callable

from django.test import TransactionTestCase

from authentik.blueprints.v1.importer import Importer


class TestTransportDocs(TransactionTestCase):
    """Empty class, test methods are added dynamically"""


def pbflow_tester(file_name: str) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestTransportDocs):
        with open(file_name, "r", encoding="utf8") as flow_json:
            importer = Importer(flow_json.read())
        self.assertTrue(importer.validate())
        self.assertTrue(importer.apply())

    return tester


for flow_file in glob("website/static/flows/*.yaml"):
    method_name = Path(flow_file).stem.replace("-", "_").replace(".", "_")
    setattr(TestTransportDocs, f"test_flow_{method_name}", pbflow_tester(flow_file))
