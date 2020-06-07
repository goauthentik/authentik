"""saml sp models"""
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Source
from passbook.core.types import UILoginButton
from passbook.crypto.models import CertificateKeyPair


class SAMLBindingTypes(models.TextChoices):
    """SAML Binding types"""

    Redirect = "REDIRECT"
    POST = "POST"


class SAMLSource(Source):
    """SAML Source"""

    issuer = models.TextField(
        blank=True,
        default=None,
        verbose_name=_("Issuer"),
        help_text=_("Also known as Entity ID. Defaults the Metadata URL."),
    )

    idp_url = models.URLField(
        verbose_name=_("IDP URL"),
        help_text=_(
            "URL that the initial SAML Request is sent to. Also known as a Binding."
        ),
    )
    binding_type = models.CharField(
        max_length=100,
        choices=SAMLBindingTypes.choices,
        default=SAMLBindingTypes.Redirect,
    )

    idp_logout_url = models.URLField(
        default=None, blank=True, null=True, verbose_name=_("IDP Logout URL")
    )
    auto_logout = models.BooleanField(default=False)

    signing_kp = models.ForeignKey(
        CertificateKeyPair,
        default=None,
        null=True,
        help_text=_(
            "Certificate Key Pair of the IdP which Assertions are validated against."
        ),
        on_delete=models.SET_NULL,
    )

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

    def __str__(self):
        return f"SAML Source {self.name}"

    class Meta:

        verbose_name = _("SAML Source")
        verbose_name_plural = _("SAML Sources")
