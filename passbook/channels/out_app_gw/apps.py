"""passbook Application Security Gateway app"""
from django.apps import AppConfig


class PassbookApplicationApplicationGatewayConfig(AppConfig):
    """passbook app_gw app"""

    name = "passbook.channels.out_app_gw"
    label = "passbook_channels_out_app_gw"
    verbose_name = "passbook Outlets.Application Security Gateway"
    mountpoint = "application/gateway/"
