"""passbook Recovery app config"""
from django.apps import AppConfig


class PassbookRecoveryConfig(AppConfig):
    """passbook Recovery app config"""

    name = 'passbook.recovery'
    label = 'passbook_recovery'
    verbose_name = 'passbook Recovery'
    mountpoint = 'recovery/'
