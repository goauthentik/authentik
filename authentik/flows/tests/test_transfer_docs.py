"""test example flows in docs"""
from glob import glob
from pathlib import Path
from typing import Callable

from django.test import TransactionTestCase

from authentik.flows.transfer.importer import FlowImporter


class TestTransferDocs(TransactionTestCase):
    """Empty class, test methods are added dynamically"""


def pbflow_tester(file_name: str) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestTransferDocs):
        with open(file_name, "r", encoding="utf8") as flow_json:
            importer = FlowImporter(flow_json.read())
        self.assertTrue(importer.validate())
        self.assertTrue(importer.apply())

    return tester


for flow_file in glob("website/static/flows/*.akflow"):
    method_name = Path(flow_file).stem.replace("-", "_").replace(".", "_")
    setattr(TestTransferDocs, f"test_flow_{method_name}", pbflow_tester(flow_file))
