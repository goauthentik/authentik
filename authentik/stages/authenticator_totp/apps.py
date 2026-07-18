"""TOTP"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorTOTPConfig(ManagedAppConfig):
    """TOTP App config"""

    name = "authentik.stages.authenticator_totp"
    label = "authentik_stages_authenticator_totp"
    verbose_name = "authentik Stages.Authenticator.TOTP"
    default = True
