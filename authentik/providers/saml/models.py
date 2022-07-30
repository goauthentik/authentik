"""authentik saml_idp Models"""
from typing import Optional

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.models import PropertyMapping, Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.utils.time import timedelta_string_validator
from authentik.sources.saml.processors.constants import (
    DSA_SHA1,
    RSA_SHA1,
    RSA_SHA256,
    RSA_SHA384,
    RSA_SHA512,
    SHA1,
    SHA256,
    SHA384,
    SHA512,
)

LOGGER = get_logger()


class SAMLBindings(models.TextChoices):
    """SAML Bindings supported by authentik"""

    REDIRECT = "redirect"
    POST = "post"


class SAMLProvider(Provider):
    """SAML 2.0 Endpoint for applications which support SAML."""

    acs_url = models.URLField(verbose_name=_("ACS URL"))
    audience = models.TextField(
        default="",
        blank=True,
        help_text=_(
            (
                "Value of the audience restriction field of the assertion. When left empty, "
                "no audience restriction will be added."
            )
        ),
    )
    issuer = models.TextField(help_text=_("Also known as EntityID"), default="authentik")
    sp_binding = models.TextField(
        choices=SAMLBindings.choices,
        default=SAMLBindings.REDIRECT,
        verbose_name=_("Service Provider Binding"),
        help_text=_(
            ("This determines how authentik sends the response back to the Service Provider.")
        ),
    )

    name_id_mapping = models.ForeignKey(
        "SAMLPropertyMapping",
        default=None,
        blank=True,
        null=True,
        on_delete=models.SET_DEFAULT,
        verbose_name=_("NameID Property Mapping"),
        help_text=_(
            (
                "Configure how the NameID value will be created. When left empty, "
                "the NameIDPolicy of the incoming request will be considered"
            )
        ),
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
        choices=(
            (SHA1, _("SHA1")),
            (SHA256, _("SHA256")),
            (SHA384, _("SHA384")),
            (SHA512, _("SHA512")),
        ),
        default=SHA256,
    )
    signature_algorithm = models.CharField(
        max_length=50,
        choices=(
            (RSA_SHA1, _("RSA-SHA1")),
            (RSA_SHA256, _("RSA-SHA256")),
            (RSA_SHA384, _("RSA-SHA384")),
            (RSA_SHA512, _("RSA-SHA512")),
            (DSA_SHA1, _("DSA-SHA1")),
        ),
        default=RSA_SHA256,
    )

    verification_kp = models.ForeignKey(
        CertificateKeyPair,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            (
                "When selected, incoming assertion's Signatures will be validated against this "
                "certificate. To allow unsigned Requests, leave on default."
            )
        ),
        on_delete=models.SET_NULL,
        verbose_name=_("Verification Certificate"),
        related_name="+",
    )
    signing_kp = models.ForeignKey(
        CertificateKeyPair,
        default=None,
        null=True,
        blank=True,
        help_text=_("Keypair used to sign outgoing Responses going to the Service Provider."),
        on_delete=models.SET_NULL,
        verbose_name=_("Signing Keypair"),
    )

    @property
    def launch_url(self) -> Optional[str]:
        """Use IDP-Initiated SAML flow as launch URL"""
        try:
            # pylint: disable=no-member
            return reverse(
                "authentik_providers_saml:sso-init",
                kwargs={"application_slug": self.application.slug},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.saml.api import SAMLProviderSerializer

        return SAMLProviderSerializer

    @property
    def component(self) -> str:
        return "ak-provider-saml-form"

    def __str__(self):
        return f"SAML Provider {self.name}"

    class Meta:

        verbose_name = _("SAML Provider")
        verbose_name_plural = _("SAML Providers")


class SAMLPropertyMapping(PropertyMapping):
    """Map User/Group attribute to SAML Attribute, which can be used by the Service Provider."""

    saml_name = models.TextField(verbose_name="SAML Name")
    friendly_name = models.TextField(default=None, blank=True, null=True)

    @property
    def component(self) -> str:
        return "ak-property-mapping-saml-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.saml.api import SAMLPropertyMappingSerializer

        return SAMLPropertyMappingSerializer

    def __str__(self):
        name = self.friendly_name if self.friendly_name != "" else self.saml_name
        return f"{self.name} ({name})"

    class Meta:

        verbose_name = _("SAML Property Mapping")
        verbose_name_plural = _("SAML Property Mappings")
