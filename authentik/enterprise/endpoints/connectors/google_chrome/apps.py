"""authentik endpoints app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseEndpointsConnectorGoogleChromeAppConfig(EnterpriseConfig):
    """authentik endpoints app config"""

    name = "authentik.enterprise.endpoints.connectors.google_chrome"
    label = "authentik_endpoints_connectors_google_chrome"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Google Chrome"
    default = True
