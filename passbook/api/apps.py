"""passbook API AppConfig"""

from django.apps import AppConfig


class PassbookAPIConfig(AppConfig):
    """passbook API Config"""

    name = 'passbook.api'
    label = 'passbook_api'
    mountpoint = 'api/'
    verbose_name = 'passbook API'
