"""saml sp models"""
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Source
from passbook.core.types import UILoginButton
from passbook.crypto.models import CertificateKeyPair
from passbook.providers.saml.utils.time import timedelta_string_validator


class SAMLBindingTypes(models.TextChoices):
    """SAML Binding types"""

    Redirect = "REDIRECT"
    POST = "POST"


class SAMLSource(Source):
    """Authenticate using an external SAML Identity Provider."""

    issuer = models.TextField(
        blank=True,
        default=None,
        verbose_name=_("Issuer"),
        help_text=_("Also known as Entity ID. Defaults the Metadata URL."),
    )

    sso_url = models.URLField(
        verbose_name=_("SSO URL"),
        help_text=_("URL that the initial Login request is sent to."),
    )
    binding_type = models.CharField(
        max_length=100,
        choices=SAMLBindingTypes.choices,
        default=SAMLBindingTypes.Redirect,
    )

    slo_url = models.URLField(
        default=None,
        blank=True,
        null=True,
        verbose_name=_("SLO URL"),
        help_text=_("Optional URL if your IDP supports Single-Logout."),
    )

    temporary_user_delete_after = models.TextField(
        default="days=1",
        verbose_name=_("Delete temporary users after"),
        validators=[timedelta_string_validator],
        help_text=_(
            (
                "Time offset when temporary users should be deleted. This only applies if your IDP "
                "uses the NameID Format 'transient', and the user doesn't log out manually. "
                "(Format: hours=1;minutes=2;seconds=3)."
            )
        ),
    )

    signing_kp = models.ForeignKey(
        CertificateKeyPair,
        verbose_name=_("Singing Keypair"),
        help_text=_(
            "Certificate Key Pair of the IdP which Assertion's Signature is validated against."
        ),
        on_delete=models.PROTECT,
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
