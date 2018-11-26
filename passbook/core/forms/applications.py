"""passbook Core Application forms"""
from django import forms

from passbook.core.models import Application


class ApplicationForm(forms.ModelForm):
    """Application Form"""

    class Meta:

        model = Application
        fields = ['name', 'launch_url', 'icon_url', 'rules', 'provider', 'skip_authorization']
        widgets = {
            'name': forms.TextInput(),
            'launch_url': forms.TextInput(),
            'icon_url': forms.TextInput(),
        }
