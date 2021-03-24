"""TOTP"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikStageAuthenticatorTOTPConfig(AppConfig):
    """TOTP App config"""

    name = "authentik.stages.authenticator_totp"
    label = "authentik_stages_authenticator_totp"
    verbose_name = "authentik Stages.Authenticator.TOTP"

    def ready(self):
        import_module("authentik.stages.authenticator_totp.signals")
