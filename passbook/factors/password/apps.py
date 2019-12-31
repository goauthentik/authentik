"""passbook core app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookFactorPasswordConfig(AppConfig):
    """passbook password factor config"""

    name = "passbook.factors.password"
    label = "passbook_factors_password"
    verbose_name = "passbook Factors.Password"

    def ready(self):
        import_module("passbook.factors.password.signals")
