from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderMicrosoftEntraConfig(EnterpriseConfig):

    name = "authentik.enterprise.providers.microsoft_entra"
    label = "authentik_providers_microsoft_entra"
    verbose_name = "authentik Enterprise.Providers.Microsoft Entra"
    default = True
