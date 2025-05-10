"""saml sp models"""

from typing import Any

from django.db import models
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.common.expression.evaluator import BaseEvaluator
from authentik.common.models import DomainlessURLValidator
from authentik.common.saml.constants import (
    DSA_SHA1,
    ECDSA_SHA1,
    ECDSA_SHA256,
    ECDSA_SHA384,
    ECDSA_SHA512,
    NS_SAML_ASSERTION,
    RSA_SHA1,
    RSA_SHA256,
    RSA_SHA384,
    RSA_SHA512,
    SAML_ATTRIBUTES_GROUP,
    SAML_BINDING_POST,
    SAML_BINDING_REDIRECT,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_WINDOWS,
    SAML_NAME_ID_FORMAT_X509,
    SHA1,
    SHA256,
    SHA384,
    SHA512,
)
from authentik.common.utils.time import timedelta_string_validator
from authentik.core.models import (
    GroupSourceConnection,
    PropertyMapping,
    Source,
    UserSourceConnection,
)
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.challenge import RedirectChallenge
from authentik.flows.models import Flow


class SAMLBindingTypes(models.TextChoices):
    """SAML Binding types"""

    REDIRECT = "REDIRECT", _("Redirect Binding")
    POST = "POST", _("POST Binding")
    POST_AUTO = "POST_AUTO", _("POST Binding with auto-confirmation")

    @property
    def uri(self) -> str:
        """Convert database field to URI"""
        return {
            SAMLBindingTypes.POST: SAML_BINDING_POST,
            SAMLBindingTypes.POST_AUTO: SAML_BINDING_POST,
            SAMLBindingTypes.REDIRECT: SAML_BINDING_REDIRECT,
        }[self]


class SAMLNameIDPolicy(models.TextChoices):
    """SAML NameID Policies"""

    EMAIL = SAML_NAME_ID_FORMAT_EMAIL
    PERSISTENT = SAML_NAME_ID_FORMAT_PERSISTENT
    X509 = SAML_NAME_ID_FORMAT_X509
    WINDOWS = SAML_NAME_ID_FORMAT_WINDOWS
    TRANSIENT = SAML_NAME_ID_FORMAT_TRANSIENT


class SAMLSource(Source):
    """Authenticate using an external SAML Identity Provider."""

    pre_authentication_flow = models.ForeignKey(
        Flow,
        on_delete=models.CASCADE,
        help_text=_("Flow used before authentication."),
        related_name="source_pre_authentication",
    )

    issuer = models.TextField(
        blank=True,
        default=None,
        verbose_name=_("Issuer"),
        help_text=_("Also known as Entity ID. Defaults the Metadata URL."),
    )

    sso_url = models.TextField(
        validators=[DomainlessURLValidator(schemes=("http", "https"))],
        verbose_name=_("SSO URL"),
        help_text=_("URL that the initial Login request is sent to."),
    )
    slo_url = models.TextField(
        validators=[DomainlessURLValidator(schemes=("http", "https"))],
        default=None,
        blank=True,
        null=True,
        verbose_name=_("SLO URL"),
        help_text=_("Optional URL if your IDP supports Single-Logout."),
    )

    allow_idp_initiated = models.BooleanField(
        default=False,
        help_text=_(
            "Allows authentication flows initiated by the IdP. This can be a security risk, "
            "as no validation of the request ID is done."
        ),
    )
    name_id_policy = models.TextField(
        choices=SAMLNameIDPolicy.choices,
        default=SAMLNameIDPolicy.PERSISTENT,
        help_text=_(
            "NameID Policy sent to the IdP. Can be unset, in which case no Policy is sent."
        ),
    )
    binding_type = models.CharField(
        max_length=100,
        choices=SAMLBindingTypes.choices,
        default=SAMLBindingTypes.REDIRECT,
    )

    temporary_user_delete_after = models.TextField(
        default="days=1",
        verbose_name=_("Delete temporary users after"),
        validators=[timedelta_string_validator],
        help_text=_(
            "Time offset when temporary users should be deleted. This only applies if your IDP "
            "uses the NameID Format 'transient', and the user doesn't log out manually. "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
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
        help_text=_("Keypair used to sign outgoing Responses going to the Identity Provider."),
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

    @property
    def component(self) -> str:
        return "ak-source-saml-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.saml.api.source import SAMLSourceSerializer

        return SAMLSourceSerializer

    @property
    def property_mapping_type(self) -> type[PropertyMapping]:
        return SAMLSourcePropertyMapping

    def get_base_user_properties(self, root: Any, name_id: Any, **kwargs):
        attributes = {}
        assertion = root.find(f"{{{NS_SAML_ASSERTION}}}Assertion")
        if assertion is None:
            raise ValueError("Assertion element not found")
        attribute_statement = assertion.find(f"{{{NS_SAML_ASSERTION}}}AttributeStatement")
        if attribute_statement is None:
            raise ValueError("Attribute statement element not found")
        # Get all attributes and their values into a dict
        for attribute in attribute_statement.iterchildren():
            key = attribute.attrib["Name"]
            attributes.setdefault(key, [])
            for value in attribute.iterchildren():
                attributes[key].append(value.text)
        if SAML_ATTRIBUTES_GROUP in attributes:
            attributes["groups"] = attributes[SAML_ATTRIBUTES_GROUP]
            del attributes[SAML_ATTRIBUTES_GROUP]
        # Flatten all lists in the dict
        for key, value in attributes.items():
            if key == "groups":
                continue
            attributes[key] = BaseEvaluator.expr_flatten(value)
        attributes["username"] = name_id.text

        return attributes

    def get_base_group_properties(self, group_id: str, **kwargs):
        return {
            "name": group_id,
        }

    def get_issuer(self, request: HttpRequest) -> str:
        """Get Source's Issuer, falling back to our Metadata URL if none is set"""
        if self.issuer is None:
            return self.build_full_url(request, view="metadata")
        return self.issuer

    def build_full_url(self, request: HttpRequest, view: str = "acs") -> str:
        """Build Full ACS URL to be used in IDP"""
        return request.build_absolute_uri(
            reverse(f"authentik_sources_saml:{view}", kwargs={"source_slug": self.slug})
        )

    @property
    def icon_url(self) -> str:
        icon = super().icon_url
        if not icon:
            return static("authentik/sources/saml.png")
        return icon

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        return UILoginButton(
            challenge=RedirectChallenge(
                data={
                    "to": reverse(
                        "authentik_sources_saml:login",
                        kwargs={"source_slug": self.slug},
                    ),
                }
            ),
            name=self.name,
            icon_url=self.icon_url,
        )

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-saml",
                "configure_url": reverse(
                    "authentik_sources_saml:login",
                    kwargs={"source_slug": self.slug},
                ),
                "icon_url": self.icon_url,
            }
        )

    def __str__(self):
        return f"SAML Source {self.name}"

    class Meta:
        verbose_name = _("SAML Source")
        verbose_name_plural = _("SAML Sources")


class SAMLSourcePropertyMapping(PropertyMapping):
    """Map SAML properties to User or Group object attributes"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-saml-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.saml.api.property_mappings import SAMLSourcePropertyMappingSerializer

        return SAMLSourcePropertyMappingSerializer

    class Meta:
        verbose_name = _("SAML Source Property Mapping")
        verbose_name_plural = _("SAML Source Property Mappings")


class UserSAMLSourceConnection(UserSourceConnection):
    """Connection to configured SAML Sources."""

    @property
    def serializer(self) -> Serializer:
        from authentik.sources.saml.api.source_connection import UserSAMLSourceConnectionSerializer

        return UserSAMLSourceConnectionSerializer

    class Meta:
        verbose_name = _("User SAML Source Connection")
        verbose_name_plural = _("User SAML Source Connections")


class GroupSAMLSourceConnection(GroupSourceConnection):
    """Group-source connection"""

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.saml.api.source_connection import (
            GroupSAMLSourceConnectionSerializer,
        )

        return GroupSAMLSourceConnectionSerializer

    class Meta:
        verbose_name = _("Group SAML Source Connection")
        verbose_name_plural = _("Group SAML Source Connections")
