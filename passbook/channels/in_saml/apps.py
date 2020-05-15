"""Passbook SAML app config"""

from django.apps import AppConfig


class PassbookInletSAMLConfig(AppConfig):
    """passbook saml_idp app config"""

    name = "passbook.channels.in_saml"
    label = "passbook_channels_in_saml"
    verbose_name = "passbook Inlets.SAML"
    mountpoint = "source/saml/"
