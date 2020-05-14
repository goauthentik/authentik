"""passbook login stage app config"""
from django.apps import AppConfig


class PassbookStageUserLoginConfig(AppConfig):
    """passbook login stage config"""

    name = "passbook.stages.user_login"
    label = "passbook_stages_user_login"
    verbose_name = "passbook Stages.User Login"
