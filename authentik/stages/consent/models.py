"""authentik consent stage"""

from dataclasses import dataclass

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import Application, User
from authentik.flows.models import Stage
from authentik.lib.models import (
    ExpiringModel,
    HashedClientIDModel,
    InternallyManagedMixin,
    SerializerModel,
    hash_client_id,
)
from authentik.lib.utils.time import timedelta_string_validator


@dataclass(frozen=True, slots=True)
class ConsentClient:
    """A client of an application that consent is given to, instead of the application.

    Consent is normally given to an application, which is used through its own client. When
    an application is used by other clients, for example an OAuth2 provider that accepts
    clients besides its registered one, the integration adds a `ConsentClient` to the plan
    context. Consent is then remembered for that exact client: consent given to the
    application never applies to it, and its consent never applies to the application or to
    any other client. Instances are stored in flow plans, so they must stay picklable."""

    # Exact client identifier, never normalized
    client_id: str
    # Shown on the consent screen; never used to identify the client
    name: str | None = None
    # Host the user is sent back to, shown when it differs from the client identifier's host
    redirect_host: str | None = None


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


class UserConsent(InternallyManagedMixin, SerializerModel, ExpiringModel, HashedClientIDModel):
    """Consent given by a user for an application, or for one of its clients. The client ID
    is empty for consent given to the application itself, which only applies to the
    application's own client."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    permissions = models.TextField(default="")

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.consent.api import UserConsentSerializer

        return UserConsentSerializer

    def __str__(self):
        return f"User Consent {self.application_id} by {self.user_id}"

    @staticmethod
    def given_to_q(client: ConsentClient | None) -> models.Q:
        """Filter for consent given to `client`, or to the application itself when None"""
        if client is None:
            return models.Q(client_id_hash__isnull=True)
        return models.Q(client_id_hash=hash_client_id(client.client_id), client_id=client.client_id)

    def is_given_to(self, client: ConsentClient | None) -> bool:
        """Check whether this consent was given to exactly `client`, or to the application
        itself when None"""
        if client is None:
            return self.client_id is None
        return self.client_id == client.client_id

    class Meta:
        verbose_name = _("User Consent")
        verbose_name_plural = _("User Consents")
        indexes = ExpiringModel.Meta.indexes
        constraints = [
            # Consent given to the application itself
            models.UniqueConstraint(
                fields=["user", "application", "permissions"],
                condition=models.Q(client_id_hash__isnull=True),
                name="consent_userconsent_application_unique",
            ),
            # Consent given to a client of the application
            models.UniqueConstraint(
                fields=["user", "application", "permissions", "client_id_hash"],
                condition=models.Q(client_id_hash__isnull=False),
                name="consent_userconsent_client_unique",
            ),
        ]
