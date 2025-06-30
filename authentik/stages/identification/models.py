"""identification stage models"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Source
from authentik.flows.models import Flow, Stage
from authentik.stages.captcha.models import CaptchaStage
from authentik.stages.password.models import PasswordStage


class UserFields(models.TextChoices):
    """Fields which the user can identify themselves with"""

    E_MAIL = "email"
    USERNAME = "username"
    UPN = "upn"


class IdentificationStage(Stage):
    """Allows the user to identify themselves for authentication."""

    user_fields = ArrayField(
        models.CharField(max_length=100, choices=UserFields.choices),
        blank=True,
        help_text=_(
            "Fields of the user object to match against. (Hold shift to select multiple options)"
        ),
    )

    password_stage = models.ForeignKey(
        PasswordStage,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_(
            (
                "When set, shows a password field, instead of showing the "
                "password field as separate step."
            ),
        ),
    )

    captcha_stage = models.ForeignKey(
        CaptchaStage,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_(
            (
                "When set, adds functionality exactly like a Captcha stage, but baked into the "
                "Identification stage."
            ),
        ),
    )

    case_insensitive_matching = models.BooleanField(
        default=True,
        help_text=_("When enabled, user fields are matched regardless of their casing."),
    )
    show_matched_user = models.BooleanField(
        default=True,
        help_text=_(
            "When a valid username/email has been entered, and this option is enabled, "
            "the user's username and avatar will be shown. Otherwise, the text that the user "
            "entered will be shown"
        ),
    )
    pretend_user_exists = models.BooleanField(
        default=True,
        help_text=_(
            "When enabled, the stage will succeed and continue even when incorrect user info "
            "is entered."
        ),
    )
    enable_remember_me = models.BooleanField(
        default=False,
        help_text=_(
            "Show the user the 'Remember me on this device' toggle, allowing repeat "
            "users to skip straight to entering their password."
        ),
    )
    enrollment_flow = models.ForeignKey(
        Flow,
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        related_name="+",
        default=None,
        help_text=_("Optional enrollment flow, which is linked at the bottom of the page."),
    )
    recovery_flow = models.ForeignKey(
        Flow,
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        related_name="+",
        default=None,
        help_text=_("Optional recovery flow, which is linked at the bottom of the page."),
    )
    passwordless_flow = models.ForeignKey(
        Flow,
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        related_name="+",
        default=None,
        help_text=_("Optional passwordless flow, which is linked at the bottom of the page."),
    )

    sources = models.ManyToManyField(
        Source, default=list, help_text=_("Specify which sources should be shown."), blank=True
    )
    show_source_labels = models.BooleanField(default=False)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.identification.api import IdentificationStageSerializer

        return IdentificationStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.identification.stage import IdentificationStageView

        return IdentificationStageView

    @property
    def component(self) -> str:
        return "ak-stage-identification-form"

    class Meta:
        verbose_name = _("Identification Stage")
        verbose_name_plural = _("Identification Stages")
