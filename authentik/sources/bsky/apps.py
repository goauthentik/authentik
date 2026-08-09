from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceBskyConfig(ManagedAppConfig):
    """authentik source bsky config"""

    name = "authentik.sources.bsky"
    label = "authentik_sources_bsky"
    verbose_name = "authentik Sources.Bsky"
    mountpoint = "source/bsky/"
    default = True
