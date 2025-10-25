"""SMS"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorSMSConfig(ManagedAppConfig):
    """SMS App config"""

    name = "authentik.stages.authenticator_sms"
    label = "authentik_stages_authenticator_sms"
    verbose_name = "authentik Stages.Authenticator.SMS"
    default = True
