"""authentik mobile app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorMobileConfig(ManagedAppConfig):
    """authentik mobile config"""

    name = "authentik.stages.authenticator_mobile"
    label = "authentik_stages_authenticator_mobile"
    verbose_name = "authentik Stages.Authenticator.Mobile"
    default = True
