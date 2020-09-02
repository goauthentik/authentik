"""passbook Proxy app"""
from django.apps import AppConfig


class PassbookProviderProxyConfig(AppConfig):
    """passbook proxy app"""

    name = "passbook.providers.proxy"
    label = "passbook_providers_proxy"
    verbose_name = "passbook Providers.Proxy"
