"""passbook mod saml_idp app config"""

from django.apps.config import AppConfig


class PassbookSAMLIDPConfig(AppConfig):
    """passbook saml_idp app config"""

    name = 'passbook.saml_idp'
    label = 'passbook_saml_idp'
    verbose_name = 'passbook SAML IDP'
