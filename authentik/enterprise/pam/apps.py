from authentik.enterprise.apps import EnterpriseConfig


class AuthentikPAMConfig(EnterpriseConfig):
    """PAM app config"""

    name = "authentik.enterprise.pam"
    label = "authentik_pam"
    verbose_name = "authentik Enterprise.PAM"
    default = True
