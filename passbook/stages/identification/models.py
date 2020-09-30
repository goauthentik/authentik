"""identification stage models"""
from typing import Type

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from passbook.flows.models import Flow, Stage


class UserFields(models.TextChoices):
    """Fields which the user can identify themselves with"""

    E_MAIL = "email"
    USERNAME = "username"


class Templates(models.TextChoices):
    """Templates to be used for the stage"""

    DEFAULT_LOGIN = "stages/identification/login.html"
    DEFAULT_RECOVERY = "stages/identification/recovery.html"


class IdentificationStage(Stage):
    """Allows the user to identify themselves for authentication."""

    user_fields = ArrayField(
        models.CharField(max_length=100, choices=UserFields.choices),
        help_text=_(
            (
                "Fields of the user object to match against. "
                "(Hold shift to select multiple options)"
            )
        ),
    )
    template = models.TextField(choices=Templates.choices)

    case_insensitive_matching = models.BooleanField(
        default=True,
        help_text=_(
            "When enabled, user fields are matched regardless of their casing."
        ),
    )

    enrollment_flow = models.ForeignKey(
        Flow,
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        related_name="+",
        default=None,
        help_text=_(
            "Optional enrollment flow, which is linked at the bottom of the page."
        ),
    )
    recovery_flow = models.ForeignKey(
        Flow,
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        related_name="+",
        default=None,
        help_text=_(
            "Optional recovery flow, which is linked at the bottom of the page."
        ),
    )

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.stages.identification.api import IdentificationStageSerializer

        return IdentificationStageSerializer

    @property
    def type(self) -> Type[View]:
        from passbook.stages.identification.stage import IdentificationStageView

        return IdentificationStageView

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.stages.identification.forms import IdentificationStageForm

        return IdentificationStageForm

    def __str__(self):
        return f"Identification Stage {self.name}"

    class Meta:

        verbose_name = _("Identification Stage")
        verbose_name_plural = _("Identification Stages")
