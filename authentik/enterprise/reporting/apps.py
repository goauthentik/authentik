"""Reporting app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseReporting(EnterpriseConfig):
    """authentik enterprise reporting app config"""

    name = "authentik.enterprise.reporting"
    label = "authentik_reporting"
    verbose_name = "authentik Enterprise.Reporting"
    default = True
