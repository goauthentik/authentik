"""passbook login stage app config"""
from django.apps import AppConfig


class PassbookStageLoginConfig(AppConfig):
    """passbook login stage config"""

    name = "passbook.stages.login"
    label = "passbook_stages_login"
    verbose_name = "passbook Stages.Login"
