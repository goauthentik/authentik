"""authentik deny stage app config"""

from django.apps import AppConfig


class AuthentikStageDenyConfig(AppConfig):
    """authentik deny stage config"""

    name = "authentik.stages.deny"
    label = "authentik_stages_deny"
    verbose_name = "authentik Stages.Deny"
