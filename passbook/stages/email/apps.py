"""passbook email stage config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookStageEmailConfig(AppConfig):
    """passbook email stage config"""

    name = "passbook.stages.email"
    label = "passbook_stages_email"
    verbose_name = "passbook Stages.Email"

    def ready(self):
        import_module("passbook.stages.email.tasks")
