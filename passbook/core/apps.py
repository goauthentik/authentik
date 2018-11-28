"""passbook core app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookCoreConfig(AppConfig):
    """passbook core app config"""

    name = 'passbook.core'
    label = 'passbook_core'
    verbose_name = 'passbook Core'

    def ready(self):
        import_module('passbook.core.rules')
