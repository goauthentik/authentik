from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPAMConfig(ManagedAppConfig):
    """PAM app config"""

    name = "authentik.pam"
    label = "authentik_pam"
    verbose_name = "authentik PAM"
    default = True
