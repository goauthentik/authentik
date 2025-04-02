"""authentik plex config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourcePlexConfig(ManagedAppConfig):
    """authentik source plex config"""

    name = "authentik.sources.plex"
    label = "authentik_sources_plex"
    verbose_name = "authentik Sources.Plex"
    default = True
