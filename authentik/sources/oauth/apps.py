"""authentik oauth_client config"""
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from structlog.stdlib import get_logger

LOGGER = get_logger()


class AuthentikSourceOAuthConfig(AppConfig):
    """authentik source.oauth config"""

    name = "authentik.sources.oauth"
    label = "authentik_sources_oauth"
    verbose_name = "authentik Sources.OAuth"
    mountpoint = "source/oauth/"

    def ready(self):
        """Load source_types from config file"""
        for source_type in settings.AUTHENTIK_SOURCES_OAUTH_TYPES:
            try:
                import_module(source_type)
                LOGGER.debug("Loaded OAuth Source Type", type=source_type)
            except ImportError as exc:
                LOGGER.debug(str(exc))
