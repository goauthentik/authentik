"""authentik delete stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageUserDeleteConfig(ManagedAppConfig):
    """authentik delete stage config"""

    name = "authentik.stages.user_delete"
    label = "authentik_stages_user_delete"
    verbose_name = "authentik Stages.User Delete"
    default = True
