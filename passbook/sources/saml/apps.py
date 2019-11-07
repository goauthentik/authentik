"""Passbook SAML app config"""

from django.apps import AppConfig


class PassbookSourceSAMLConfig(AppConfig):
    """passbook saml_idp app config"""

    name = 'passbook.sources.saml'
    label = 'passbook_sources_saml'
    verbose_name = 'passbook Sources.SAML'
    mountpoint = 'source/saml/'
