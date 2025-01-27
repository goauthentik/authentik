"""Email Authenticator"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorEmailConfig(ManagedAppConfig):
    """Email Authenticator App config"""
    name = "authentik.stages.authenticator_email"
    label = "authentik_stages_authenticator_email"
    verbose_name = "authentik Stages.Authenticator.Email"
