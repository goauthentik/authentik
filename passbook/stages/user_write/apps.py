"""passbook write stage app config"""
from django.apps import AppConfig


class PassbookStageUserWriteConfig(AppConfig):
    """passbook write stage config"""

    name = "passbook.stages.user_write"
    label = "passbook_stages_user_write"
    verbose_name = "passbook Stages.User Write"
