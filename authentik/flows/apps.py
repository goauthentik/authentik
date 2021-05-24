"""authentik flows app config"""
from importlib import import_module

from django.apps import AppConfig
from django.db.utils import ProgrammingError

from authentik.lib.utils.reflection import all_subclasses


class AuthentikFlowsConfig(AppConfig):
    """authentik flows app config"""

    name = "authentik.flows"
    label = "authentik_flows"
    mountpoint = "flows/"
    verbose_name = "authentik Flows"

    def ready(self):
        import_module("authentik.flows.signals")
        try:
            from authentik.flows.models import Stage

            for stage in all_subclasses(Stage):
                _ = stage().type
        except ProgrammingError:
            pass
