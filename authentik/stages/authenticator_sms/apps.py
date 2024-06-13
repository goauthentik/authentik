"""SMS"""

from django.apps import AppConfig


class AuthentikStageAuthenticatorSMSConfig(AppConfig):
    """SMS App config"""

    name = "authentik.stages.authenticator_sms"
    label = "authentik_stages_authenticator_sms"
    verbose_name = "authentik Stages.Authenticator.SMS"
