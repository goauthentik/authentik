"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEnterpriseEndpointsConnectorGoogleChromeAppConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.enterprise.endpoints.connectors.google_chrome"
    label = "authentik_endpoints_connectors_google_chrome"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Google Chrome"
    default = True
