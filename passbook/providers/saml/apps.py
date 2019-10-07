"""passbook mod saml_idp app config"""
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from structlog import get_logger

LOGGER = get_logger()

class PassbookProviderSAMLConfig(AppConfig):
    """passbook saml_idp app config"""

    name = 'passbook.providers.saml'
    label = 'passbook_providers_saml'
    verbose_name = 'passbook Providers.SAML'
    mountpoint = 'application/saml/'

    def ready(self):
        """Load source_types from config file"""
        for source_type in settings.PASSBOOK_PROVIDERS_SAML_PROCESSORS:
            try:
                import_module(source_type)
                LOGGER.info("Loaded SAML Processor", processor_class=source_type)
            except ImportError as exc:
                LOGGER.debug(exc)
