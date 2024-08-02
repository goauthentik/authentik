"""authentik Endpoint app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorEndpointConfig(ManagedAppConfig):
    """authentik endpoint config"""

    name = "authentik.stages.authenticator_endpoint"
    label = "authentik_stages_authenticator_endpoint"
    verbose_name = "authentik Stages.Authenticator.Endpoint"
    default = True
    mountpoint = "authenticators/device_trust/"
