from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderRadiusConfig(EnterpriseConfig):

    name = "authentik.enterprise.providers.radius"
    label = "authentik_enterprise_providers_radius"
    verbose_name = "authentik Enterprise.Providers.Radius"
    default = True
