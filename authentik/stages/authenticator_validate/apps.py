"""Authenticator Validation Stage"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorValidateConfig(ManagedAppConfig):
    """Authenticator Validation Stage"""

    name = "authentik.stages.authenticator_validate"
    label = "authentik_stages_authenticator_validate"
    verbose_name = "authentik Stages.Authenticator.Validate"
    default = True
