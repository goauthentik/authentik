"""passbook consent stage"""
from django.db import models
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View

from passbook.core.models import Application, ExpiringModel, User
from passbook.flows.models import Stage
from passbook.lib.utils.time import timedelta_string_validator


class ConsentMode(models.TextChoices):
    """Modes a Consent Stage can operate in"""

    ALWAYS_REQUIRE = "always_require"
    PERMANENT = "permanent"
    EXPIRING = "expiring"


class ConsentStage(Stage):
    """Prompt the user for confirmation."""

    mode = models.TextField(
        choices=ConsentMode.choices, default=ConsentMode.ALWAYS_REQUIRE
    )
    consent_expire_in = models.TextField(
        validators=[timedelta_string_validator],
        default="weeks=4",
        verbose_name="Consent expires in",
        help_text=_(
            (
                "Offset after which consent expires. "
                "(Format: hours=1;minutes=2;seconds=3)."
            )
        ),
    )

    def type(self) -> Type[View]:
        from passbook.stages.consent.stage import ConsentStageView

        return ConsentStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.consent.forms import ConsentStageForm

        return ConsentStageForm

    def __str__(self):
        return f"Consent Stage {self.name}"

    class Meta:

        verbose_name = _("Consent Stage")
        verbose_name_plural = _("Consent Stages")


class UserConsent(ExpiringModel):
    """Consent given by a user for an application"""

    # TODO: Remove related_name when oidc provider is v2
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pb_consent")
    application = models.ForeignKey(Application, on_delete=models.CASCADE)

    def __str__(self):
        return f"User Consent {self.application} by {self.user}"

    class Meta:

        unique_together = (("user", "application"),)
        verbose_name = _("User Consent")
        verbose_name_plural = _("User Consents")
