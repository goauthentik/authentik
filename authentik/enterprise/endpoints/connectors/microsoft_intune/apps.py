"""authentik endpoints app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseEndpointsConnectorMicrosoftIntuneAppConfig(EnterpriseConfig):
    """authentik endpoints app config"""

    name = "authentik.enterprise.endpoints.connectors.microsoft_intune"
    label = "authentik_endpoints_connectors_microsoft_intune"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Microsoft Intune"
    default = True
