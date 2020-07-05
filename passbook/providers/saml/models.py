"""passbook saml_idp Models"""
from typing import Optional

from django.db import models
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils.translation import ugettext_lazy as _
from structlog import get_logger

from passbook.core.models import PropertyMapping, Provider
from passbook.crypto.models import CertificateKeyPair
from passbook.lib.utils.reflection import class_to_path, path_to_class
from passbook.lib.utils.template import render_to_string
from passbook.providers.saml.processors.base import Processor
from passbook.providers.saml.utils.time import timedelta_string_validator

LOGGER = get_logger()


class SAMLBindings(models.TextChoices):
    """SAML Bindings supported by passbook"""

    REDIRECT = "redirect"
    POST = "post"


class SAMLProvider(Provider):
    """SAML 2.0 Endpoint for applications which support SAML."""

    name = models.TextField()
    processor_path = models.CharField(max_length=255, choices=[])

    acs_url = models.URLField(verbose_name=_("ACS URL"))
    audience = models.TextField(default="")
    issuer = models.TextField(help_text=_("Also known as EntityID"))
    sp_binding = models.TextField(
        choices=SAMLBindings.choices,
        default=SAMLBindings.REDIRECT,
        verbose_name=_("Service Prodier Binding"),
    )

    assertion_valid_not_before = models.TextField(
        default="minutes=-5",
        validators=[timedelta_string_validator],
        help_text=_(
            (
                "Assertion valid not before current time + this value "
                "(Format: hours=-1;minutes=-2;seconds=-3)."
            )
        ),
    )
    assertion_valid_not_on_or_after = models.TextField(
        default="minutes=5",
        validators=[timedelta_string_validator],
        help_text=_(
            (
                "Assertion not valid on or after current time + this value "
                "(Format: hours=1;minutes=2;seconds=3)."
            )
        ),
    )

    session_valid_not_on_or_after = models.TextField(
        default="minutes=86400",
        validators=[timedelta_string_validator],
        help_text=_(
            (
                "Session not valid on or after current time + this value "
                "(Format: hours=1;minutes=2;seconds=3)."
            )
        ),
    )

    digest_algorithm = models.CharField(
        max_length=50,
        choices=(("sha1", _("SHA1")), ("sha256", _("SHA256")),),
        default="sha256",
    )
    signature_algorithm = models.CharField(
        max_length=50,
        choices=(
            ("rsa-sha1", _("RSA-SHA1")),
            ("rsa-sha256", _("RSA-SHA256")),
            ("ecdsa-sha256", _("ECDSA-SHA256")),
            ("dsa-sha1", _("DSA-SHA1")),
        ),
        default="rsa-sha256",
    )

    signing_kp = models.ForeignKey(
        CertificateKeyPair,
        default=None,
        null=True,
        help_text=_("Singing is enabled upon selection of a Key Pair."),
        on_delete=models.SET_NULL,
        verbose_name=_("Signing Keypair"),
    )

    require_signing = models.BooleanField(
        default=False,
        help_text=_(
            "Require Requests to be signed by an X509 Certificate. "
            "Must match the Certificate selected in `Singing Keypair`."
        ),
    )

    form = "passbook.providers.saml.forms.SAMLProviderForm"
    _processor = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("processor_path").choices = get_provider_choices()

    @property
    def processor(self) -> Optional[Processor]:
        """Return selected processor as instance"""
        if not self._processor:
            try:
                self._processor = path_to_class(self.processor_path)(self)
            except ImportError as exc:
                LOGGER.warning(exc)
                self._processor = None
        return self._processor

    def __str__(self):
        return self.name

    def link_download_metadata(self):
        """Get link to download XML metadata for admin interface"""
        try:
            # pylint: disable=no-member
            return reverse(
                "passbook_providers_saml:metadata",
                kwargs={"application_slug": self.application.slug},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    def html_metadata_view(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with to view Metadata without downloading it"""
        from passbook.providers.saml.views import DescriptorDownloadView

        try:
            # pylint: disable=no-member
            metadata = DescriptorDownloadView.get_metadata(request, self)
            return render_to_string(
                "providers/saml/admin_metadata_modal.html",
                {"provider": self, "metadata": metadata},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    class Meta:

        verbose_name = _("SAML Provider")
        verbose_name_plural = _("SAML Providers")


class SAMLPropertyMapping(PropertyMapping):
    """Map User/Group attribute to SAML Attribute, which can be used by the Service Provider."""

    saml_name = models.TextField(verbose_name="SAML Name")
    friendly_name = models.TextField(default=None, blank=True, null=True)

    form = "passbook.providers.saml.forms.SAMLPropertyMappingForm"

    def __str__(self):
        return f"SAML Property Mapping {self.saml_name}"

    class Meta:

        verbose_name = _("SAML Property Mapping")
        verbose_name_plural = _("SAML Property Mappings")


def get_provider_choices():
    """Return tuple of class_path, class name of all providers."""
    return [
        (class_to_path(x), x.__name__) for x in getattr(Processor, "__subclasses__")()
    ]
