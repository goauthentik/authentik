"""authentik flows invitation forms"""
from django import forms

from authentik.admin.fields import CodeMirrorWidget, YAMLField
from authentik.stages.invitation.models import Invitation, InvitationStage


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
        widgets = {"fixed_data": CodeMirrorWidget()}
        field_classes = {"fixed_data": YAMLField}
