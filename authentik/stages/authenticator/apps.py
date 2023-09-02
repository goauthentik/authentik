"""Authenticator"""
from django.apps import AppConfig


class AuthentikStageAuthenticatorConfig(AppConfig):
    """Authenticator App config"""

    name = "authentik.stages.authenticator"
    label = "authentik_stages_authenticator"
    verbose_name = "authentik Stages.Authenticator"
