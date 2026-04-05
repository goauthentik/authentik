"""authentik Recovery app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikRecoveryConfig(ManagedAppConfig):
    """authentik Recovery app config"""

    name = "authentik.recovery"
    label = "authentik_recovery"
    verbose_name = "authentik Recovery"
    mountpoint = "recovery/"
    default = True
