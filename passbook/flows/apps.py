"""passbook flows app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookFlowsConfig(AppConfig):
    """passbook flows app config"""

    name = "passbook.flows"
    label = "passbook_flows"
    mountpoint = "flows/"
    verbose_name = "passbook Flows"

    def ready(self):
        import_module("passbook.flows.signals")
