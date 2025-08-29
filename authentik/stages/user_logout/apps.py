"""authentik logout stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageUserLogoutConfig(ManagedAppConfig):
    """authentik logout stage config"""

    name = "authentik.stages.user_logout"
    label = "authentik_stages_user_logout"
    verbose_name = "authentik Stages.User Logout"
    default = True
