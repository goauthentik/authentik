"""Authenticator"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.reflection import all_subclasses


class AuthentikStageAuthenticatorConfig(ManagedAppConfig):
    """Authenticator App config"""

    name = "authentik.stages.authenticator"
    label = "authentik_stages_authenticator"
    verbose_name = "authentik Stages.Authenticator"
    default = True

    def reconcile_global_load_devices(self):
        """Ensure all devices are loaded"""
        from authentik.stages.authenticator.models import Device

        for device in all_subclasses(Device):
            if device._meta.abstract:
                continue
            _ = device().validator
