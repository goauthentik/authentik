from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderApplePSSOConfig(EnterpriseConfig):

    name = "authentik.enterprise.providers.apple_psso"
    label = "authentik_providers_apple_psso"
    verbose_name = "authentik Enterprise.Providers.Apple Platform SSO"
    default = True
    mountpoints = {
        "authentik.enterprise.providers.apple_psso.urls": "application/apple_psso/",
        "authentik.enterprise.providers.apple_psso.urls_root": "",
    }
