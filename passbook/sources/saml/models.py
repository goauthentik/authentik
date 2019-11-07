"""saml sp models"""
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from passbook.core.models import Source


class SAMLSource(Source):
    """SAML2 Source"""

    entity_id = models.TextField(blank=True, default=None)
    idp_url = models.URLField()
    idp_logout_url = models.URLField(default=None, blank=True, null=True)
    auto_logout = models.BooleanField(default=False)
    signing_cert = models.TextField()

    form = 'passbook.sources.saml.forms.SAMLSourceForm'

    @property
    def login_button(self):
        url = reverse_lazy('passbook_sources_saml:login', kwargs={'source': self.slug})
        return url, '', self.name

    @property
    def additional_info(self):
        metadata_url = reverse_lazy('passbook_sources_saml:metadata', kwargs={
            'source': self
        })
        return f"<a href=\"{metadata_url}\" class=\"btn btn-default btn-sm\">Metadata Download</a>"

    class Meta:

        verbose_name = _('SAML Source')
        verbose_name_plural = _('SAML Sources')
