"""passbook core invitation form"""

from django import forms

from passbook.core.models import Invite


class InviteForm(forms.ModelForm):
    """InviteForm"""

    class Meta:

        model = Invite
        fields = '__all__'
