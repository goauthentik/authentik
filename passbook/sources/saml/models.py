"""saml sp models"""
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from passbook.core.types import UILoginButton
from passbook.core.models import Source


class SAMLSource(Source):
    """SAML Source"""

    entity_id = models.TextField(blank=True, default=None, verbose_name=_("Entity ID"))

    idp_url = models.URLField(verbose_name=_("IDP URL"))
    idp_logout_url = models.URLField(
        default=None, blank=True, null=True, verbose_name=_("IDP Logout URL")
    )
    auto_logout = models.BooleanField(default=False)
    signing_cert = models.TextField()

    form = "passbook.sources.saml.forms.SAMLSourceForm"

    @property
    def ui_login_button(self) -> UILoginButton:
        return UILoginButton(
            name=self.name,
            url=reverse_lazy(
                "passbook_sources_saml:login", kwargs={"source_slug": self.slug}
            ),
            icon_path="",
        )

    @property
    def ui_additional_info(self) -> str:
        metadata_url = reverse_lazy(
            "passbook_sources_saml:metadata", kwargs={"source_slug": self.slug}
        )
        return f'<a href="{metadata_url}" class="btn btn-default btn-sm">Metadata Download</a>'

    class Meta:

        verbose_name = _("SAML Source")
        verbose_name_plural = _("SAML Sources")
