from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderOAuth2Config(EnterpriseConfig):

    name = "authentik.enterprise.providers.oauth2"
    label = "authentik_enterprise_providers_oauth2"
    verbose_name = "authentik Enterprise.Providers.OAuth2"
    default = True
    mountpoint = "application/o/"
