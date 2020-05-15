"""passbook saml provider app config"""
from django.apps import AppConfig


class PassbookOutletSAMLv2Config(AppConfig):
    """passbook samlv2 provider app config"""

    name = "passbook.channels.out_samlv2"
    label = "passbook_channels_out_samlv2"
    verbose_name = "passbook Outlets.SAMLv2"
    mountpoint = "application/samlv2/"
