"""passbook email factor config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookFactorEmailConfig(AppConfig):
    """passbook email factor config"""

    name = 'passbook.factors.email'
    label = 'passbook_factors_email'
    verbose_name = 'passbook Factors.Email'

    def ready(self):
        import_module('passbook.factors.email.tasks')
