"""Email"""

from django.apps import AppConfig


class AuthentikStageAuthenticatorEmailConfig(AppConfig):
    """Email App config"""

    name = "authentik.stages.authenticator_email"
    label = "authentik_stages_authenticator_email"
    verbose_name = "authentik Stages.Authenticator.Email"
