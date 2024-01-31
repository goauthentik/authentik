"""authentik logout stage app config"""

from django.apps import AppConfig


class AuthentikStageUserLogoutConfig(AppConfig):
    """authentik logout stage config"""

    name = "authentik.stages.user_logout"
    label = "authentik_stages_user_logout"
    verbose_name = "authentik Stages.User Logout"
