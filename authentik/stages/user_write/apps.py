"""authentik write stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageUserWriteConfig(ManagedAppConfig):
    """authentik write stage config"""

    name = "authentik.stages.user_write"
    label = "authentik_stages_user_write"
    verbose_name = "authentik Stages.User Write"
    default = True
