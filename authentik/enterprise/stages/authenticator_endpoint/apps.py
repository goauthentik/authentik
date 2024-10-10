"""authentik Endpoint app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikStageAuthenticatorEndpointConfig(EnterpriseConfig):
    """authentik endpoint config"""

    name = "authentik.enterprise.stages.authenticator_endpoint"
    label = "authentik_stages_authenticator_endpoint"
    verbose_name = "authentik Enterprise.Stages.Authenticator.Endpoint"
    default = True
    mountpoint = "authenticators/endpoint/"
