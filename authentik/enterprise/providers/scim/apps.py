from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderSCIMConfig(EnterpriseConfig):

    name = "authentik.enterprise.providers.scim"
    label = "authentik_enterprise_providers_scim"
    verbose_name = "authentik Enterprise.Providers.SCIM"
    default = True
