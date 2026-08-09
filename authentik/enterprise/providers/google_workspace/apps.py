from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderGoogleConfig(EnterpriseConfig):

    name = "authentik.enterprise.providers.google_workspace"
    label = "authentik_providers_google_workspace"
    verbose_name = "authentik Enterprise.Providers.Google Workspace"
    default = True
