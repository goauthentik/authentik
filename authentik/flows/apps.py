"""authentik flows app config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikFlowsConfig(AppConfig):
    """authentik flows app config"""

    name = "authentik.flows"
    label = "authentik_flows"
    mountpoint = "flows/"
    verbose_name = "authentik Flows"

    def ready(self):
        import_module("authentik.flows.signals")
