"""authentik login stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageUserLoginConfig(ManagedAppConfig):
    """authentik login stage config"""

    name = "authentik.stages.user_login"
    label = "authentik_stages_user_login"
    verbose_name = "authentik Stages.User Login"
    default = True
