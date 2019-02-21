"""passbook Core Application forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Application, Provider


class ApplicationForm(forms.ModelForm):
    """Application Form"""

    provider = forms.ModelChoiceField(queryset=Provider.objects.all().select_subclasses(),
                                      required=False)

    class Meta:

        model = Application
        fields = ['name', 'slug', 'launch_url', 'icon_url',
                  'policies', 'provider', 'skip_authorization']
        widgets = {
            'name': forms.TextInput(),
            'launch_url': forms.TextInput(),
            'icon_url': forms.TextInput(),
        }
        labels = {
            'launch_url': _('Launch URL'),
            'icon_url': _('Icon URL'),
        }
