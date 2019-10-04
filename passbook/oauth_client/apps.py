"""passbook oauth_client config"""
from importlib import import_module

from django.apps import AppConfig
from structlog import get_logger

from passbook.lib.config import CONFIG

LOGGER = get_logger()

class PassbookOAuthClientConfig(AppConfig):
    """passbook oauth_client config"""

    name = 'passbook.oauth_client'
    label = 'passbook_oauth_client'
    verbose_name = 'passbook OAuth Client'
    mountpoint = 'source/oauth/'

    def ready(self):
        """Load source_types from config file"""
        source_types_to_load = CONFIG.y('oauth_client.types', [])
        for source_type in source_types_to_load:
            try:
                import_module(source_type)
                LOGGER.info("Loaded %s", source_type)
            except ImportError as exc:
                LOGGER.debug(exc)
