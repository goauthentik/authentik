"""authentik Recovery app config"""

from django.apps import AppConfig


class AuthentikRecoveryConfig(AppConfig):
    """authentik Recovery app config"""

    name = "authentik.recovery"
    label = "authentik_recovery"
    verbose_name = "authentik Recovery"
    mountpoint = "recovery/"
