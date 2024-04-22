from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderGoogleConfig(EnterpriseConfig):

    name = "authentik.enterprise.providers.google"
    label = "authentik_providers_google"
    verbose_name = "authentik Enterprise.Providers.Google"
    default = True
