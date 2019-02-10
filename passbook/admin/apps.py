"""passbook admin app config"""
from django.apps import AppConfig


class PassbookAdminConfig(AppConfig):
    """passbook admin app config"""

    name = 'passbook.admin'
    label = 'passbook_admin'
    mountpoint = 'administration/'
    verbose_name = 'passbook Admin'
