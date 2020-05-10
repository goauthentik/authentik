"""passbook logout stage app config"""
from django.apps import AppConfig


class PassbookStageUserLogoutConfig(AppConfig):
    """passbook logout stage config"""

    name = "passbook.stages.user_logout"
    label = "passbook_stages_user_logout"
    verbose_name = "passbook Stages.User Logout"
