"""authentik duo app config"""
from django.apps import AppConfig


class AuthentikStageAuthenticatorDuoConfig(AppConfig):
    """authentik duo config"""

    name = "authentik.stages.authenticator_duo"
    label = "authentik_stages_authenticator_duo"
    verbose_name = "authentik Stages.Authenticator.Duo"
