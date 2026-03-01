"""authentik Endpoint app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEndpointsConnectorGoogleChromeAppConfig(EnterpriseConfig):
    """authentik endpoint config"""

    name = "authentik.enterprise.endpoints.connectors.google_chrome"
    label = "authentik_endpoints_connectors_google_chrome"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Google Chrome"
    default = True
    mountpoint = "endpoints/google/"
