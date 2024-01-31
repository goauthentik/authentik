"""authentik write stage app config"""

from django.apps import AppConfig


class AuthentikStageUserWriteConfig(AppConfig):
    """authentik write stage config"""

    name = "authentik.stages.user_write"
    label = "authentik_stages_user_write"
    verbose_name = "authentik Stages.User Write"
