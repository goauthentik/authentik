"""authentik stage app config"""
from django.apps import AppConfig


class AuthentikStageSourceConfig(AppConfig):
    """authentik source stage config"""

    name = "authentik.stages.source"
    label = "authentik_stages_source"
    verbose_name = "authentik Stages.Source"
