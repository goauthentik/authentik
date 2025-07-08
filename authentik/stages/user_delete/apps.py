"""authentik delete stage app config"""

from django.apps import AppConfig


class AuthentikStageUserDeleteConfig(AppConfig):
    """authentik delete stage config"""

    name = "authentik.stages.user_delete"
    label = "authentik_stages_user_delete"
    verbose_name = "authentik Stages.User Delete"
