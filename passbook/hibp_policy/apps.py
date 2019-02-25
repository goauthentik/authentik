"""Passbook hibp app config"""

from django.apps import AppConfig


class PassbookHIBPConfig(AppConfig):
    """Passbook hibp app config"""

    name = 'passbook.hibp_policy'
    label = 'passbook_hibp_policy'
    verbose_name = 'passbook HaveIBeenPwned Policy'
