"""authentik email stage config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikStageEmailConfig(AppConfig):
    """authentik email stage config"""

    name = "authentik.stages.email"
    label = "authentik_stages_email"
    verbose_name = "authentik Stages.Email"

    def ready(self):
        import_module("authentik.stages.email.tasks")
