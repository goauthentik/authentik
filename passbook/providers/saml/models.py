"""passbook saml_idp Models"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import PropertyMapping, Provider
from passbook.lib.utils.reflection import class_to_path, path_to_class
from passbook.providers.saml.base import Processor

LOGGER = get_logger()


class SAMLProvider(Provider):
    """Model to save information about a Remote SAML Endpoint"""

    name = models.TextField()
    acs_url = models.URLField()
    audience = models.TextField(default='')
    processor_path = models.CharField(max_length=255, choices=[])
    issuer = models.TextField()
    assertion_valid_for = models.IntegerField(default=86400)
    signing = models.BooleanField(default=True)
    signing_cert = models.TextField()
    signing_key = models.TextField()

    form = 'passbook.providers.saml.forms.SAMLProviderForm'
    _processor = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('processor_path').choices = get_provider_choices()

    @property
    def processor(self):
        """Return selected processor as instance"""
        if not self._processor:
            try:
                self._processor = path_to_class(self.processor_path)(self)
            except ModuleNotFoundError as exc:
                LOGGER.warning(exc)
                self._processor = None
        return self._processor

    def __str__(self):
        return "SAML Provider %s" % self.name

    def link_download_metadata(self):
        """Get link to download XML metadata for admin interface"""
        try:
            # pylint: disable=no-member
            return reverse('passbook_providers_saml:saml-metadata',
                           kwargs={'application': self.application.slug})
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    class Meta:

        verbose_name = _('SAML Provider')
        verbose_name_plural = _('SAML Providers')


class SAMLPropertyMapping(PropertyMapping):
    """SAML Property mapping, allowing Name/FriendlyName mapping to a list of strings"""

    saml_name = models.TextField()
    friendly_name = models.TextField(default=None, blank=True, null=True)
    values = ArrayField(models.TextField())

    form = 'passbook.providers.saml.forms.SAMLPropertyMappingForm'

    def __str__(self):
        return "SAML Property Mapping %s" % self.saml_name

    class Meta:

        verbose_name = _('SAML Property Mapping')
        verbose_name_plural = _('SAML Property Mappings')

def get_provider_choices():
    """Return tuple of class_path, class name of all providers."""
    return [(class_to_path(x), x.__name__) for x in Processor.__subclasses__()]
