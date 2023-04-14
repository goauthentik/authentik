"""Enterprise app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEnterpriseConfig(ManagedAppConfig):
    """Enterprise app config"""

    name = "authentik.enterprise"
    label = "authentik_enterprise"
    verbose_name = "authentik Enterprise"
    default = True
