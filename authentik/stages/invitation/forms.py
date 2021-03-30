"""authentik flows invitation forms"""
from django import forms

from authentik.stages.invitation.models import InvitationStage


class InvitationStageForm(forms.ModelForm):
    """Form to create/edit InvitationStage instances"""

    class Meta:

        model = InvitationStage
        fields = ["name", "continue_flow_without_invitation"]
        widgets = {
            "name": forms.TextInput(),
        }
