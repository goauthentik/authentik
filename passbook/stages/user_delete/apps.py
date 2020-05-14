"""passbook delete stage app config"""
from django.apps import AppConfig


class PassbookStageUserDeleteConfig(AppConfig):
    """passbook delete stage config"""

    name = "passbook.stages.user_delete"
    label = "passbook_stages_user_delete"
    verbose_name = "passbook Stages.User Delete"
