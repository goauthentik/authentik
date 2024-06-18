"""TOTP"""

from django.apps import AppConfig


class AuthentikStageAuthenticatorTOTPConfig(AppConfig):
    """TOTP App config"""

    name = "authentik.stages.authenticator_totp"
    label = "authentik_stages_authenticator_totp"
    verbose_name = "authentik Stages.Authenticator.TOTP"
