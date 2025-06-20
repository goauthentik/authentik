"""authentik dummy stage config"""

from django.apps import AppConfig


class AuthentikStageDummyConfig(AppConfig):
    """authentik dummy stage config"""

    name = "authentik.stages.dummy"
    label = "authentik_stages_dummy"
    verbose_name = "authentik Stages.Dummy"
