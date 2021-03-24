"""Authenticator Static stage"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikStageAuthenticatorStaticConfig(AppConfig):
    """Authenticator Static stage"""

    name = "authentik.stages.authenticator_static"
    label = "authentik_stages_authenticator_static"
    verbose_name = "authentik Stages.Authenticator.Static"

    def ready(self):
        import_module("authentik.stages.authenticator_static.signals")
