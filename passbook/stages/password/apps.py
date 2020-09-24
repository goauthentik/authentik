"""passbook core app config"""
from django.apps import AppConfig


class PassbookStagePasswordConfig(AppConfig):
    """passbook password stage config"""

    name = "passbook.stages.password"
    label = "passbook_stages_password"
    verbose_name = "passbook Stages.Password"
