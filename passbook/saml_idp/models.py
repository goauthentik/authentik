"""passbook saml_idp Models"""

from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Provider
from passbook.lib.utils.reflection import class_to_path
from passbook.saml_idp.base import Processor


class SAMLProvider(Provider):
    """Model to save information about a Remote SAML Endpoint"""

    name = models.TextField()
    acs_url = models.URLField()
    processor_path = models.CharField(max_length=255, choices=[])
    issuer = models.TextField()
    assertion_valid_for = models.IntegerField(default=86400)
    signing = models.BooleanField(default=True)
    signing_cert = models.TextField()
    signing_key = models.TextField()

    form = 'passbook.saml_idp.forms.SAMLProviderForm'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('processor_path').choices = get_provider_choices()

    def __str__(self):
        return "SAMLProvider %s (processor=%s)" % (self.name, self.processor_path)

    class Meta:

        verbose_name = _('SAML Provider')
        verbose_name_plural = _('SAML Providers')


def get_provider_choices():
    """Return tuple of class_path, class name of all providers."""
    return [(class_to_path(x), x.__name__) for x in Processor.__subclasses__()]
