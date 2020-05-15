"""passbook oauth_client config"""
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from structlog import get_logger

LOGGER = get_logger()


class PassbookInletOAuthConfig(AppConfig):
    """passbook source.oauth config"""

    name = "passbook.channels.in_oauth"
    label = "passbook_channels_in_oauth"
    verbose_name = "passbook Inlets.OAuth"
    mountpoint = "source/oauth/"

    def ready(self):
        """Load source_types from config file"""
        for source_type in settings.PASSBOOK_SOURCES_OAUTH_TYPES:
            try:
                import_module(source_type)
            except ImportError as exc:
                LOGGER.debug(exc)
