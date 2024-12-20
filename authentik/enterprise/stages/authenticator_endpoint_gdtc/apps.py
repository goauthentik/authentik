"""authentik Endpoint app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikStageAuthenticatorEndpointConfig(EnterpriseConfig):
    """authentik endpoint config"""

    name = "authentik.enterprise.stages.authenticator_endpoint_gdtc"
    label = "authentik_stages_authenticator_endpoint_gdtc"
    verbose_name = "authentik Enterprise.Stages.Authenticator.Endpoint GDTC"
    default = True
    mountpoint = "endpoint/gdtc/"
