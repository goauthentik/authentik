"""passbook core invitation form"""

from django import forms

from passbook.core.models import Invite


class InviteForm(forms.ModelForm):
    """InviteForm"""

    class Meta:

        model = Invite
        fields = ['created_by', 'expires', 'fixed_username', 'fixed_email']
        labels = {
            'fixed_username': "Force user's username (optional)",
            'fixed_email': "Force user's email (optional)",
        }
        widgets = {
            'created_by': forms.Select(attrs={'disabled': 'disabled'}),
            'fixed_username': forms.TextInput(),
            'fixed_email': forms.TextInput(),
        }
