"""authentik webauthn app config"""

from django.apps import AppConfig


class AuthentikStageAuthenticatorWebAuthnConfig(AppConfig):
    """authentik webauthn config"""

    name = "authentik.stages.authenticator_webauthn"
    label = "authentik_stages_authenticator_webauthn"
    verbose_name = "authentik Stages.Authenticator.WebAuthn"
