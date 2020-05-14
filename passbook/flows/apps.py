"""passbook flows app config"""
from django.apps import AppConfig


class PassbookFlowsConfig(AppConfig):
    """passbook flows app config"""

    name = "passbook.flows"
    label = "passbook_flows"
    mountpoint = "flows/"
    verbose_name = "passbook Flows"
