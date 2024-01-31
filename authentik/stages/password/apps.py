"""authentik core app config"""

from django.apps import AppConfig


class AuthentikStagePasswordConfig(AppConfig):
    """authentik password stage config"""

    name = "authentik.stages.password"
    label = "authentik_stages_password"
    verbose_name = "authentik Stages.Password"
