"""passbook core authentication forms"""

from django import forms
from django.core.validators import validate_email

from passbook.lib.config import CONFIG


class LoginForm(forms.Form):
    """Allow users to login"""

    uid_field = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    remember_me = forms.BooleanField(required=False)

    def clean_uid_field(self):
        """Validate uid_field after EmailValidator if 'email' is the only selected uid_fields"""
        if CONFIG.y('passbook.uid_fields') == ['email']:
            validate_email(self.cleaned_data.get('uid_field'))
        return self.cleaned_data.get('uid_field')
