"""Kerberos Provider"""
from typing import Optional, Type

from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Provider
from authentik.lib.generators import generate_key
from authentik.providers.kerberos.lib.crypto import SUPPORTED_ENCTYPES
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator


def _get_kerberos_enctypes():
    """Get supported Kerberos encryption types as a model choices list"""
    return [(enctype.ENC_TYPE.value, enctype.ENC_NAME) for enctype in SUPPORTED_ENCTYPES]


def _get_default_enctypes():
    return [enctype.ENC_TYPE.value for enctype in SUPPORTED_ENCTYPES]


validate_spn = RegexValidator(
    r"@.+$",
    message=_("SPN should not contain a realm."),
    inverse_match=True,
)


class KerberosServiceMixin(models.Model):
    """Common fields and methods for Kerberos services"""

    maximum_ticket_lifetime = models.TextField(
        help_text=_("Maximum Ticket lifetime (Format: hours=1;minutes=2;seconds=3)."),
        default="days=1",
        validators=[
            timedelta_string_validator,
        ],
    )

    maximum_ticket_renew_lifetime = models.TextField(
        help_text=_("Maximum Ticket renew lifetime (Format: hours=1;minutes=2;seconds=3)."),
        default="weeks=1",
        validators=[
            timedelta_string_validator,
        ],
    )

    allowed_enctypes = ArrayField(
        models.IntegerField(choices=_get_kerberos_enctypes()),
        default=_get_default_enctypes,
        help_text=_("Allowed encryption types."),
    )

    allow_postdateable = models.BooleanField(
        default=True,
        help_text=_("Should the user be able to request a ticket with a start time in the future."),
    )

    allow_renewable = models.BooleanField(
        default=True,
        help_text=_("Should the user getting the ticket be able to renew it."),
    )

    allow_proxiable = models.BooleanField(
        default=True,
        help_text=_(
            "Should the service getting the ticket be able to use it on behalf of the user."
        ),
    )

    allow_forwardable = models.BooleanField(
        default=False,
        help_text=_(
            "Should the service getting the ticket be able to request a "
            "TGT on behalf of the user."
        ),
    )

    requires_preauth = models.BooleanField(
        default=True, help_text=_("Should tickets only be issued to preauthenticated clients.")
    )

    secret = models.TextField(
        default=generate_key, help_text=_("The secret value from which Kerberos keys are derived.")
    )

    kvno = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._secret = self.secret

    def save(self, *args, **kwargs):
        if self.secret != self._secret:
            self.kvno = (self.kvno + 1) % 2**32
            if self.kvno % 2**8 == 0:
                # Avoid having kvno8 == 0
                self.kvno += 1
        return super().save(*args, **kwargs)

    @cached_property
    def keys(self) -> dict[int, bytes]:
        """Get service keys from its secret."""
        return {
            enctype.ENC_TYPE: enctype.string_to_key(
                password=self.secret.encode("utf-8"),
                salt=str(self.pk).encode("utf-8"),
            )
            for enctype in SUPPORTED_ENCTYPES
            if enctype.ENC_TYPE.value in self.allowed_enctypes
        }


class KerberosRealm(KerberosServiceMixin, SerializerModel):
    """Kerberos Realm"""

    name = models.TextField(
        help_text=_("Kerberos realm name."),
        unique=True,
    )

    authentication_flow = models.ForeignKey(
        "authentik_flows.Flow",
        null=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "Flow used for authentication when a TGT for the associated realm is "
            "requested by a user."
        ),
    )

    maximum_skew = models.TextField(
        help_text=_(
            "Maximum allowed clock drift between the client and the server "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
        default="minutes=5",
        validators=[
            timedelta_string_validator,
        ],
    )

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Kerberos Realm")
        verbose_name_plural = _("Kerberos Realms")

    @property
    def serializer(self) -> Type[Serializer]:
        from authentik.providers.kerberos.api import KerberosRealmSerializer

        return KerberosRealmSerializer


class KerberosProvider(KerberosServiceMixin, Provider):
    """Allow applications to authenticate against authentik's users using
    Kerberos."""

    realm = models.ForeignKey(KerberosRealm, on_delete=models.CASCADE)

    service_principal_name = models.TextField(
        help_text=_("The Kerberos principal used to designate this provider, without the realm."),
        validators=[validate_spn],
    )

    set_ok_as_delegate = models.BooleanField(
        default=False,
        help_text=_(
            "Should the tickets issued for this provider have the ok-as-delegate flag set."
        ),
    )

    @property
    def launch_url(self) -> Optional[str]:
        """Kerberos never has a launch URL"""
        return None

    @property
    def component(self) -> str:
        return "ak-provider-kerberos-form"

    @property
    def serializer(self) -> Type[Serializer]:
        from authentik.providers.kerberos.api import KerberosProviderSerializer

        return KerberosProviderSerializer

    @property
    def full_spn(self) -> str:
        """Provider service principal name with realm included"""
        return f"{self.service_principal_name}@{self.realm.name}"

    def __str__(self):
        return f"Kerberos Provider {self.name}"

    class Meta:
        unique_together = (("realm", "service_principal_name"),)
        verbose_name = _("Kerberos Provider")
        verbose_name_plural = _("Kerberos Providers")
