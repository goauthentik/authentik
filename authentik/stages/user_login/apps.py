"""authentik login stage app config"""

from django.apps import AppConfig


class AuthentikStageUserLoginConfig(AppConfig):
    """authentik login stage config"""

    name = "authentik.stages.user_login"
    label = "authentik_stages_user_login"
    verbose_name = "authentik Stages.User Login"
