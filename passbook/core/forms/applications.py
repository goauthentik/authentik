"""passbook Core Application forms"""
from django import forms

from passbook.core.models import Application, Provider


class ApplicationForm(forms.ModelForm):
    """Application Form"""

    provider = forms.ModelChoiceField(queryset=Provider.objects.all().select_subclasses())

    class Meta:

        model = Application
        fields = ['name', 'slug', 'launch_url', 'icon_url',
                  'policies', 'provider', 'skip_authorization']
        widgets = {
            'name': forms.TextInput(),
            'launch_url': forms.TextInput(),
            'icon_url': forms.TextInput(),
        }
