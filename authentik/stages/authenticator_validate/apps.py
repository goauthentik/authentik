"""Authenticator Validation Stage"""

from django.apps import AppConfig


class AuthentikStageAuthenticatorValidateConfig(AppConfig):
    """Authenticator Validation Stage"""

    name = "authentik.stages.authenticator_validate"
    label = "authentik_stages_authenticator_validate"
    verbose_name = "authentik Stages.Authenticator.Validate"
