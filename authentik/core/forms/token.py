"""Core user token form"""
from django import forms

from authentik.core.models import Token


class UserTokenForm(forms.ModelForm):
    """Token form, for tokens created by endusers"""

    class Meta:

        model = Token
        fields = [
            "identifier",
            "expires",
            "expiring",
            "description",
        ]
        widgets = {
            "identifier": forms.TextInput(),
            "description": forms.TextInput(),
        }
