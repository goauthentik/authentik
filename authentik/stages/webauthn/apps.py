"""authentik webauthn app config"""
from django.apps import AppConfig


class AuthentikStageWebAuthnConfig(AppConfig):
    """authentik webauthn config"""

    name = "authentik.stages.webauthn"
    label = "authentik_stages_webauthn"
    verbose_name = "authentik Stages.WebAuthn"
    mountpoint = "-/user/webauthn/"
