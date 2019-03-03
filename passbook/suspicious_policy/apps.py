"""Passbook suspicious_policy app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookSuspiciousPolicyConfig(AppConfig):
    """Passbook suspicious_policy app config"""

    name = 'passbook.suspicious_policy'
    label = 'passbook_suspicious_policy'
    verbose_name = 'passbook Suspicious Request Detector'

    def ready(self):
        import_module('passbook.suspicious_policy.signals')
