"""passbook outposts app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookOutpostConfig(AppConfig):
    """passbook outposts app config"""

    name = "passbook.outposts"
    label = "passbook_outposts"
    verbose_name = "passbook Outpost"

    def ready(self):
        import_module("passbook.outposts.signals")
