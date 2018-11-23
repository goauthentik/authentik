"""passbook audit app"""
from django.apps import AppConfig


class PassbookAuditConfig(AppConfig):
    """passbook audit app"""

    name = 'passbook.audit'
    label = 'passbook_audit'
    mountpoint = 'audit/'
