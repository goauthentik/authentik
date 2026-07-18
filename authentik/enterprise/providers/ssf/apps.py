"""SSF app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderSSF(EnterpriseConfig):
    """authentik enterprise ssf app config"""

    name = "authentik.enterprise.providers.ssf"
    label = "authentik_providers_ssf"
    verbose_name = "authentik Enterprise.Providers.SSF"
    default = True
    mountpoint = ""
