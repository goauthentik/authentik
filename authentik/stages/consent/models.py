"""authentik consent stage"""

from dataclasses import dataclass
from hashlib import sha256
from json import dumps

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import Application, User
from authentik.flows.models import Stage
from authentik.lib.models import ExpiringModel, InternallyManagedMixin, SerializerModel
from authentik.lib.utils.time import timedelta_string_validator

# Upper bound for client identifiers and resources consent is given to. Other registration
# kinds than an application's own client may use URLs as client identifiers.
CONSENT_CLIENT_ID_MAX_LENGTH = 2048
CONSENT_RESOURCE_MAX_LENGTH = 2048


def consent_binding_hash(client_id: str | None, resource: str | None) -> str | None:
    """Fixed-length digest of the client and resource consent is given to, used to index
    and deduplicate consent. None for consent given to the application itself. The digest
    only narrows a lookup; the client identifier and resource must still be compared."""
    if client_id is None and resource is None:
        return None
    return sha256(dumps([client_id, resource]).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ConsentClient:
    """A client of an application that consent is given to, instead of the application.

    Consent is normally given to an application, which is used through its own client. When
    an application is used by other clients, for example an OAuth2 provider that accepts
    clients besides its registered one, the integration adds a `ConsentClient` to the plan
    context. Consent is then remembered for that exact client and resource: consent given to
    the application never applies to it, and its consent never applies to the application or
    to any other client. Instances are stored in flow plans, so they must stay picklable."""

    # Exact client identifier, never normalized. None when consent is given to the
    # application's own client for a specific resource.
    client_id: str | None = None
    # Resource (RFC 8707) access is requested for, if any
    resource: str | None = None
    # Shown on the consent screen; never used to identify the client
    name: str | None = None
    # Host the user is sent back to, shown when it differs from the client identifier's host
    redirect_host: str | None = None

    @property
    def binding_hash(self) -> str | None:
        return consent_binding_hash(self.client_id, self.resource)


class ConsentMode(models.TextChoices):
    """Modes a Consent Stage can operate in"""

    ALWAYS_REQUIRE = "always_require"
    PERMANENT = "permanent"
    EXPIRING = "expiring"


class ConsentStage(Stage):
    """Prompt the user for confirmation."""

    mode = models.TextField(choices=ConsentMode.choices, default=ConsentMode.EXPIRING)
    consent_expire_in = models.TextField(
        validators=[timedelta_string_validator],
        default="weeks=4",
        verbose_name="Consent expires in",
        help_text=_("Offset after which consent expires. (Format: hours=1;minutes=2;seconds=3)."),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.consent.api import ConsentStageSerializer

        return ConsentStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.consent.stage import ConsentStageView

        return ConsentStageView

    @property
    def component(self) -> str:
        return "ak-stage-consent-form"

    class Meta:
        verbose_name = _("Consent Stage")
        verbose_name_plural = _("Consent Stages")


class UserConsent(InternallyManagedMixin, SerializerModel, ExpiringModel):
    """Consent given by a user for an application"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    permissions = models.TextField(default="")
    # Client and resource consent was given to. Both are empty for consent given to the
    # application itself, which only applies to the application's own client.
    client_id = models.CharField(
        max_length=CONSENT_CLIENT_ID_MAX_LENGTH,
        null=True,
        default=None,
        verbose_name=_("Client ID"),
    )
    resource = models.CharField(
        max_length=CONSENT_RESOURCE_MAX_LENGTH,
        null=True,
        default=None,
        verbose_name=_("Resource"),
    )
    binding_hash = models.CharField(max_length=64, null=True, default=None, editable=False)

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.consent.api import UserConsentSerializer

        return UserConsentSerializer

    def __str__(self):
        return f"User Consent {self.application_id} by {self.user_id}"

    def save(self, *args, **kwargs):
        self.binding_hash = consent_binding_hash(self.client_id, self.resource)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and {"client_id", "resource"} & set(update_fields):
            kwargs["update_fields"] = set(update_fields) | {"binding_hash"}
        return super().save(*args, **kwargs)

    @staticmethod
    def given_to_q(client: ConsentClient | None) -> models.Q:
        """Filter for consent given to `client`, or to the application itself when None.
        Narrows by the indexed hash; results must be verified with `is_given_to()`."""
        if client is None or client.binding_hash is None:
            return models.Q(binding_hash__isnull=True)
        return models.Q(
            binding_hash=client.binding_hash,
            client_id=client.client_id,
            resource=client.resource,
        )

    def is_given_to(self, client: ConsentClient | None) -> bool:
        """Check whether this consent was given to exactly `client`, or to the application
        itself when None"""
        if client is None:
            return self.client_id is None and self.resource is None
        return self.client_id == client.client_id and self.resource == client.resource

    class Meta:
        verbose_name = _("User Consent")
        verbose_name_plural = _("User Consents")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["user", "application", "binding_hash"]),
        ]
        constraints = [
            # Consent given to the application itself
            models.UniqueConstraint(
                fields=["user", "application", "permissions"],
                condition=models.Q(binding_hash__isnull=True),
                name="consent_userconsent_application_unique",
            ),
            # Consent given to a client of the application
            models.UniqueConstraint(
                fields=["user", "application", "permissions", "binding_hash"],
                condition=models.Q(binding_hash__isnull=False),
                name="consent_userconsent_client_unique",
            ),
        ]
