"""passbook Application Security Gateway app"""
from django.apps import AppConfig


class PassbookApplicationApplicationGatewayConfig(AppConfig):
    """passbook app_gw app"""

    name = 'passbook.app_gw'
    label = 'passbook_app_gw'
    verbose_name = 'passbook Application Security Gateway'
    mountpoint = 'app_gw/'
