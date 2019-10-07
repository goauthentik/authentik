"""passbook core app config"""
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from structlog import get_logger

LOGGER = get_logger()


class PassbookCoreConfig(AppConfig):
    """passbook core app config"""

    name = 'passbook.core'
    label = 'passbook_core'
    verbose_name = 'passbook Core'
    mountpoint = ''

    def ready(self):
        for factors_to_load in settings.PASSBOOK_CORE_FACTORS:
            try:
                import_module(factors_to_load)
                LOGGER.info("Loaded factor", factor_class=factors_to_load)
            except ImportError as exc:
                LOGGER.debug(exc)
