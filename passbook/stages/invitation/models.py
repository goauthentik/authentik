"""invitation stage models"""
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import User
from passbook.flows.models import Stage
from passbook.lib.models import UUIDModel


class InvitationStage(Stage):
    """Invitation stage, to enroll themselves with enforced parameters"""

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

    type = "passbook.stages.invitation.stage.InvitationStageView"
    form = "passbook.stages.invitation.forms.InvitationStageForm"

    def __str__(self):
        return f"Invitation Stage {self.name}"

    class Meta:

        verbose_name = _("Invitation Stage")
        verbose_name_plural = _("Invitation Stages")


class Invitation(UUIDModel):
    """Single-use invitation link"""

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    expires = models.DateTimeField(default=None, blank=True, null=True)
    fixed_data = JSONField(default=dict)

    def __str__(self):
        return f"Invitation {self.uuid.hex} created by {self.created_by}"

    class Meta:

        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")
