"""passbook create stage app config"""
from django.apps import AppConfig


class PassbookStageUserCreateConfig(AppConfig):
    """passbook create stage config"""

    name = "passbook.stages.user_create"
    label = "passbook_stages_user_create"
    verbose_name = "passbook Stages.User Create"
