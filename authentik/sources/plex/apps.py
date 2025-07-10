"""authentik plex config"""

from django.apps import AppConfig


class AuthentikSourcePlexConfig(AppConfig):
    """authentik source plex config"""

    name = "authentik.sources.plex"
    label = "authentik_sources_plex"
    verbose_name = "authentik Sources.Plex"
