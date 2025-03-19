from authentik.blueprints.apps import ManagedAppConfig


class AuthentikChannelsConfig(ManagedAppConfig):
    name = "authentik.channels"
    label = "authentik_channels"
    verbose_name = "authentik Channels"
    default = True
