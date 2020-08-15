"""passbook flows invitation forms"""
from django import forms
from django.utils.translation import gettext as _

from passbook.admin.fields import CodeMirrorWidget, YAMLField
from passbook.stages.invitation.models import Invitation, InvitationStage


class InvitationStageForm(forms.ModelForm):
    """Form to create/edit InvitationStage instances"""

    class Meta:

        model = InvitationStage
        fields = ["name", "continue_flow_without_invitation"]
        widgets = {
            "name": forms.TextInput(),
        }


class InvitationForm(forms.ModelForm):
    """InvitationForm"""

    class Meta:

        model = Invitation
        fields = ["expires", "fixed_data"]
        labels = {
            "fixed_data": _("Optional fixed data to enforce on user enrollment."),
        }
        widgets = {"fixed_data": CodeMirrorWidget()}
        field_classes = {"fixed_data": YAMLField}
