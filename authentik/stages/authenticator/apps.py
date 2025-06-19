"""Authenticator"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorConfig(ManagedAppConfig):
    """Authenticator App config"""

    name = "authentik.stages.authenticator"
    label = "authentik_stages_authenticator"
    verbose_name = "authentik Stages.Authenticator"
    default = True
