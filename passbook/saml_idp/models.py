"""passbook saml_idp Models"""

from django.db import models

from passbook.core.models import Application
from passbook.lib.utils.reflection import class_to_path
from passbook.saml_idp.base import Processor


class SAMLApplication(Application):
    """Model to save information about a Remote SAML Endpoint"""

    acs_url = models.URLField()
    processor_path = models.CharField(max_length=255, choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        processors = [(class_to_path(x), x.__name__) for x in Processor.__subclasses__()]
        self._meta.get_field('processor_path').choices = processors

    def __str__(self):
        return "SAMLApplication %s (processor=%s)" % (self.name, self.processor_path)

    def user_is_authorized(self):
        raise NotImplementedError()
