"""RAC app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEnterpriseRAC(ManagedAppConfig):
    """authentik enterprise rac app config"""

    name = "authentik.enterprise.rac"
    label = "authentik_enterprise_rac"
    verbose_name = "authentik Enterprise.RAC"
    default = True
    mountpoint = ""
    ws_mountpoint = "authentik.enterprise.rac.urls"
