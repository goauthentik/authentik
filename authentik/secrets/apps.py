"""Managed secrets app configuration."""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSecretsConfig(ManagedAppConfig):
    """Managed secrets app configuration."""

    name = "authentik.secrets"
    label = "authentik_secrets"
    verbose_name = "authentik Secrets"
    default = True
