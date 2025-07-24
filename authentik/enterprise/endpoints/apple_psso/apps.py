from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseEndpointsApplePSSOConfig(EnterpriseConfig):

    name = "authentik.enterprise.endpoints.apple_psso"
    label = "authentik_endpoints_apple_psso"
    verbose_name = "authentik Enterprise.Endpoints.Apple Platform SSO"
    default = True
    mountpoints = {
        "authentik.enterprise.endpoints.apple_psso.urls": "endpoint/apple/sso/",
        "authentik.enterprise.endpoints.apple_psso.urls_root": "",
    }
