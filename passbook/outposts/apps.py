"""passbook outposts app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookOutpostConfig(AppConfig):
    """passbook outposts app config"""

    name = "passbook.outposts"
    label = "passbook_outposts"
    # mountpoint = "outposts/"
    verbose_name = "passbook Outpost"

    def ready(self):
        """Flow signals that clear the cache"""
        import_module("passbook.outposts.signals")
