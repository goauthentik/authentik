"""invitation stage models"""
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import ExpiringModel, User
from authentik.flows.models import Stage
from authentik.lib.models import SerializerModel


class InvitationStage(Stage):
    """Simplify enrollment; allow users to use a single
    link to create their user with pre-defined parameters."""

    continue_flow_without_invitation = models.BooleanField(
        default=False,
        help_text=_(
            "If this flag is set, this Stage will jump to the next Stage when "
            "no Invitation is given. By default this Stage will cancel the "
            "Flow when no invitation is given."
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.invitation.api import InvitationStageSerializer

        return InvitationStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.invitation.stage import InvitationStageView

        return InvitationStageView

    @property
    def component(self) -> str:
        return "ak-stage-invitation-form"

    class Meta:
        verbose_name = _("Invitation Stage")
        verbose_name_plural = _("Invitation Stages")


class Invitation(SerializerModel, ExpiringModel):
    """Single-use invitation link"""

    invite_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.SlugField()

    flow = models.ForeignKey(
        "authentik_flows.Flow",
        default=None,
        null=True,
        on_delete=models.SET_DEFAULT,
        help_text=_("When set, only the configured flow can use this invitation."),
    )
    single_use = models.BooleanField(
        default=False,
        help_text=_("When enabled, the invitation will be deleted after usage."),
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    fixed_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Optional fixed data to enforce on user enrollment."),
    )

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.invitation.api import InvitationSerializer

        return InvitationSerializer

    def __str__(self):
        return f"Invitation {str(self.invite_uuid)} created by {self.created_by}"

    class Meta:
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")
