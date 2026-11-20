"""OAuth2 CIMD app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderOAuth2CIMDConfig(EnterpriseConfig):
    """authentik enterprise OAuth2 Client ID Metadata Document app config"""

    name = "authentik.enterprise.providers.oauth2_cimd"
    label = "authentik_providers_oauth2_cimd"
    verbose_name = "authentik Enterprise.Providers.OAuth2 CIMD"
    default = True
