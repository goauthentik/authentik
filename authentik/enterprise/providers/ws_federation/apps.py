"""WSFed app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderWSFederatopm(EnterpriseConfig):
    """authentik enterprise ws federation app config"""

    name = "authentik.enterprise.providers.ws_federation"
    label = "authentik_providers_ws_federation"
    verbose_name = "authentik Enterprise.Providers.WS-Federation"
    default = True
    mountpoint = "application/wsfed/"
