"""passbook mod saml_idp app config"""
from importlib import import_module
from logging import getLogger

from django.apps import AppConfig

from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)

class PassbookSAMLIDPConfig(AppConfig):
    """passbook saml_idp app config"""

    name = 'passbook.saml_idp'
    label = 'passbook_saml_idp'
    verbose_name = 'passbook SAML IDP'

    def ready(self):
        """Load source_types from config file"""
        source_types_to_load = CONFIG.y('saml_idp.types', [])
        for source_type in source_types_to_load:
            try:
                import_module(source_type)
                LOGGER.info("Loaded %s", source_type)
            except ImportError as exc:
                LOGGER.debug(exc)
