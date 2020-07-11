"""passbook SAML IdP app config"""

from django.apps import AppConfig


class PassbookProviderSAMLConfig(AppConfig):
    """passbook SAML IdP app config"""

    name = "passbook.providers.saml"
    label = "passbook_providers_saml"
    verbose_name = "passbook Providers.SAML"
    mountpoint = "application/saml/"
