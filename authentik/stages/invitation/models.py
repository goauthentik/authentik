"""invitation stage models"""
from typing import Type
from uuid import uuid4

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.models import User
from authentik.flows.models import Stage


class InvitationStage(Stage):
    """Simplify enrollment; allow users to use a single
    link to create their user with pre-defined parameters."""

    continue_flow_without_invitation = models.BooleanField(
        default=False,
        help_text=_(
            (
                "If this flag is set, this Stage will jump to the next Stage when "
                "no Invitation is given. By default this Stage will cancel the "
                "Flow when no invitation is given."
            )
        ),
    )

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.invitation.api import InvitationStageSerializer

        return InvitationStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.invitation.stage import InvitationStageView

        return InvitationStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.invitation.forms import InvitationStageForm

        return InvitationStageForm

    def __str__(self):
        return f"Invitation Stage {self.name}"

    class Meta:

        verbose_name = _("Invitation Stage")
        verbose_name_plural = _("Invitation Stages")


class Invitation(models.Model):
    """Single-use invitation link"""

    invite_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    expires = models.DateTimeField(default=None, blank=True, null=True)
    fixed_data = models.JSONField(default=dict)

    def __str__(self):
        return f"Invitation {self.invite_uuid.hex} created by {self.created_by}"

    class Meta:

        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")
