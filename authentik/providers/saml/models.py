"""authentik SAML Provider Models"""

from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    DSA_SHA1,
    ECDSA_SHA1,
    ECDSA_SHA256,
    ECDSA_SHA384,
    ECDSA_SHA512,
    RSA_SHA1,
    RSA_SHA256,
    RSA_SHA384,
    RSA_SHA512,
    SHA1,
    SHA256,
    SHA384,
    SHA512,
)
from authentik.core.api.object_types import CreatableType
from authentik.core.models import PropertyMapping, Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.models import DomainlessURLValidator
from authentik.lib.utils.time import timedelta_string_validator

LOGGER = get_logger()


class SAMLBindings(models.TextChoices):
    """SAML Bindings supported by authentik"""

    REDIRECT = "redirect"
    POST = "post"


class SAMLProvider(Provider):
    """SAML 2.0 Endpoint for applications which support SAML."""

    acs_url = models.TextField(
        validators=[DomainlessURLValidator(schemes=("http", "https"))], verbose_name=_("ACS URL")
    )
    audience = models.TextField(
        default="",
        blank=True,
        help_text=_(
            "Value of the audience restriction field of the assertion. When left empty, "
            "no audience restriction will be added."
        ),
    )
    issuer = models.TextField(help_text=_("Also known as EntityID"), default="authentik")
    sp_binding = models.TextField(
        choices=SAMLBindings.choices,
        default=SAMLBindings.REDIRECT,
        verbose_name=_("Service Provider Binding"),
        help_text=_(
            "This determines how authentik sends the response back to the Service Provider."
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
            "Configure how the NameID value will be created. When left empty, "
            "the NameIDPolicy of the incoming request will be considered"
        ),
    )
    authn_context_class_ref_mapping = models.ForeignKey(
        "SAMLPropertyMapping",
        default=None,
        blank=True,
        null=True,
        on_delete=models.SET_DEFAULT,
        verbose_name=_("AuthnContextClassRef Property Mapping"),
        related_name="+",
        help_text=_(
            "Configure how the AuthnContextClassRef value will be created. When left empty, "
            "the AuthnContextClassRef will be set based on which authentication methods the user "
            "used to authenticate."
        ),
    )

    assertion_valid_not_before = models.TextField(
        default="minutes=-5",
        validators=[timedelta_string_validator],
        help_text=_(
            "Assertion valid not before current time + this value "
            "(Format: hours=-1;minutes=-2;seconds=-3)."
        ),
    )
    assertion_valid_not_on_or_after = models.TextField(
        default="minutes=5",
        validators=[timedelta_string_validator],
        help_text=_(
            "Assertion not valid on or after current time + this value "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
    )

    session_valid_not_on_or_after = models.TextField(
        default="minutes=86400",
        validators=[timedelta_string_validator],
        help_text=_(
            "Session not valid on or after current time + this value "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
    )

    digest_algorithm = models.TextField(
        choices=(
            (SHA1, _("SHA1")),
            (SHA256, _("SHA256")),
            (SHA384, _("SHA384")),
            (SHA512, _("SHA512")),
        ),
        default=SHA256,
    )
    signature_algorithm = models.TextField(
        choices=(
            (RSA_SHA1, _("RSA-SHA1")),
            (RSA_SHA256, _("RSA-SHA256")),
            (RSA_SHA384, _("RSA-SHA384")),
            (RSA_SHA512, _("RSA-SHA512")),
            (ECDSA_SHA1, _("ECDSA-SHA1")),
            (ECDSA_SHA256, _("ECDSA-SHA256")),
            (ECDSA_SHA384, _("ECDSA-SHA384")),
            (ECDSA_SHA512, _("ECDSA-SHA512")),
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
            "When selected, incoming assertion's Signatures will be validated against this "
            "certificate. To allow unsigned Requests, leave on default."
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
    encryption_kp = models.ForeignKey(
        CertificateKeyPair,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            "When selected, incoming assertions are encrypted by the IdP using the public "
            "key of the encryption keypair. The assertion is decrypted by the SP using the "
            "the private key."
        ),
        on_delete=models.SET_NULL,
        verbose_name=_("Encryption Keypair"),
        related_name="+",
    )

    default_relay_state = models.TextField(
        default="", blank=True, help_text=_("Default relay_state value for IDP-initiated logins")
    )

    sign_assertion = models.BooleanField(default=True)
    sign_response = models.BooleanField(default=False)

    @property
    def launch_url(self) -> str | None:
        """Use IDP-Initiated SAML flow as launch URL"""
        try:
            return reverse(
                "authentik_providers_saml:sso-init",
                kwargs={"application_slug": self.application.slug},
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/saml.png")

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.saml.api.providers import SAMLProviderSerializer

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
    """Map User/Group attribute to SAML Attribute, which can be used by the Service Provider"""

    saml_name = models.TextField(verbose_name="SAML Name")
    friendly_name = models.TextField(default=None, blank=True, null=True)

    @property
    def component(self) -> str:
        return "ak-property-mapping-provider-saml-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.saml.api.property_mappings import SAMLPropertyMappingSerializer

        return SAMLPropertyMappingSerializer

    def __str__(self):
        name = self.friendly_name if self.friendly_name != "" else self.saml_name
        return f"{self.name} ({name})"

    class Meta:
        verbose_name = _("SAML Provider Property Mapping")
        verbose_name_plural = _("SAML Provider Property Mappings")


class SAMLProviderImportModel(CreatableType, Provider):
    """Create a SAML Provider by importing its Metadata."""

    @property
    def component(self):
        return "ak-provider-saml-import-form"

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/saml.png")

    class Meta:
        abstract = True
        verbose_name = _("SAML Provider from Metadata")
        verbose_name_plural = _("SAML Providers from Metadata")
