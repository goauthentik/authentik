"""passbook core invitation form"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from passbook.core.models import Invitation, User


class InvitationForm(forms.ModelForm):
    """InvitationForm"""

    def clean_fixed_username(self):
        """Check if username is already used"""
        username = self.cleaned_data.get('fixed_username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_('Username is already in use.'))
        return username

    def clean_fixed_email(self):
        """Check if email is already used"""
        email = self.cleaned_data.get('fixed_email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('E-Mail is already in use.'))
        return email

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
