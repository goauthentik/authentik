"""passbook audit app"""
from importlib import import_module

from django.apps import AppConfig


class PassbookAuditConfig(AppConfig):
    """passbook audit app"""

    name = 'passbook.audit'
    label = 'passbook_audit'
    verbose_name = 'passbook Audit'
    mountpoint = 'audit/'

    def ready(self):
        import_module('passbook.audit.signals')
