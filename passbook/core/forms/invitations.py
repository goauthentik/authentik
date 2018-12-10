"""passbook core invitation form"""

from django import forms

from passbook.core.models import Invitation


class InvitationForm(forms.ModelForm):
    """InvitationForm"""

    class Meta:

        model = Invitation
        fields = ['expires', 'fixed_username', 'fixed_email']
        labels = {
            'fixed_username': "Force user's username (optional)",
            'fixed_email': "Force user's email (optional)",
        }
        widgets = {
            'fixed_username': forms.TextInput(),
            'fixed_email': forms.TextInput(),
        }
