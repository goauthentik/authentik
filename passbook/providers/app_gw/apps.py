"""passbook Application Security Gateway app"""
from django.apps import AppConfig


class PassbookApplicationApplicationGatewayConfig(AppConfig):
    """passbook app_gw app"""

    name = "passbook.providers.app_gw"
    label = "passbook_providers_app_gw"
    verbose_name = "passbook Providers.Application Security Gateway"
    mountpoint = "application/gateway/"
