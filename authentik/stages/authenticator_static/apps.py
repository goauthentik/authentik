"""Authenticator Static stage"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorStaticConfig(ManagedAppConfig):
    """Authenticator Static stage"""

    name = "authentik.stages.authenticator_static"
    label = "authentik_stages_authenticator_static"
    verbose_name = "authentik Stages.Authenticator.Static"
    default = True

    def reconcile_load_stages_authenticator_static_signals(self):
        """Load stages.authenticator_static signals"""
        self.import_module("authentik.stages.authenticator_static.signals")
