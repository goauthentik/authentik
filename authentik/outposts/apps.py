"""authentik outposts app config"""
from importlib import import_module

from django.apps import AppConfig
from structlog.stdlib import get_logger

LOGGER = get_logger()


class AuthentikOutpostConfig(AppConfig):
    """authentik outposts app config"""

    name = "authentik.outposts"
    label = "authentik_outposts"
    verbose_name = "authentik Outpost"

    def ready(self):
        import_module("authentik.outposts.signals")
        import_module("authentik.outposts.managed")
