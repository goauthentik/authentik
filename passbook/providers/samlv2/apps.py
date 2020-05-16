"""passbook saml provider app config"""
from django.apps import AppConfig


class PassbookProviderSAMLv2Config(AppConfig):
    """passbook samlv2 provider app config"""

    name = "passbook.providers.samlv2"
    label = "passbook_providers_samlv2"
    verbose_name = "passbook Providers.SAMLv2"
    mountpoint = "application/samlv2/"
