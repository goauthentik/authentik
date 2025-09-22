"""authentik consent stage"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import Application, ExpiringModel, User
from authentik.flows.models import Stage
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator


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


class UserConsent(SerializerModel, ExpiringModel):
    """Consent given by a user for an application"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    permissions = models.TextField(default="")

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.consent.api import UserConsentSerializer

        return UserConsentSerializer

    def __str__(self):
        return f"User Consent {self.application_id} by {self.user_id}"

    class Meta:
        unique_together = (("user", "application", "permissions"),)
        verbose_name = _("User Consent")
        verbose_name_plural = _("User Consents")
        indexes = ExpiringModel.Meta.indexes
