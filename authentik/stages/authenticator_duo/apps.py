"""authentik duo app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageAuthenticatorDuoConfig(ManagedAppConfig):
    """authentik duo config"""

    name = "authentik.stages.authenticator_duo"
    label = "authentik_stages_authenticator_duo"
    verbose_name = "authentik Stages.Authenticator.Duo"
    default = True
