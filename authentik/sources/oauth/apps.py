"""authentik oauth_client config"""
from importlib import import_module

from django.apps import AppConfig
from structlog.stdlib import get_logger

LOGGER = get_logger()

AUTHENTIK_SOURCES_OAUTH_TYPES = [
    "authentik.sources.oauth.types.apple",
    "authentik.sources.oauth.types.azure_ad",
    "authentik.sources.oauth.types.discord",
    "authentik.sources.oauth.types.facebook",
    "authentik.sources.oauth.types.github",
    "authentik.sources.oauth.types.google",
    "authentik.sources.oauth.types.oidc",
    "authentik.sources.oauth.types.okta",
    "authentik.sources.oauth.types.reddit",
    "authentik.sources.oauth.types.twitter",
    "authentik.sources.oauth.types.mailcow",
]


class AuthentikSourceOAuthConfig(AppConfig):
    """authentik source.oauth config"""

    name = "authentik.sources.oauth"
    label = "authentik_sources_oauth"
    verbose_name = "authentik Sources.OAuth"
    mountpoint = "source/oauth/"

    def ready(self):
        """Load source_types from config file"""
        for source_type in AUTHENTIK_SOURCES_OAUTH_TYPES:
            try:
                import_module(source_type)
            except ImportError as exc:
                LOGGER.warning("Failed to load OAuth Source", exc=exc)
