"""passbook core app config"""
from importlib import import_module

from django.apps import AppConfig
from structlog import get_logger

from passbook.lib.config import CONFIG

LOGGER = get_logger()

class PassbookCoreConfig(AppConfig):
    """passbook core app config"""

    name = 'passbook.core'
    label = 'passbook_core'
    verbose_name = 'passbook Core'
    mountpoint = ''

    def ready(self):
        import_module('passbook.policy.engine')
        factors_to_load = CONFIG.y('passbook.factors', [])
        for factors_to_load in factors_to_load:
            try:
                import_module(factors_to_load)
                LOGGER.info("Loaded %s", factors_to_load)
            except ImportError as exc:
                LOGGER.debug(exc)
