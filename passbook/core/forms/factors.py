"""passbook administration forms"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.core.models import DummyFactor, PasswordFactor
from passbook.lib.fields import DynamicArrayField

GENERAL_FIELDS = ['name', 'slug', 'order', 'policies', 'enabled']

class PasswordFactorForm(forms.ModelForm):
    """Form to create/edit Password Factors"""

    class Meta:

        model = PasswordFactor
        fields = GENERAL_FIELDS + ['backends', 'password_policies']
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
            'policies': FilteredSelectMultiple(_('policies'), False)
        }
        field_classes = {
            'backends': DynamicArrayField
        }

class DummyFactorForm(forms.ModelForm):
    """Form to create/edit Dummy Factor"""

    class Meta:

        model = DummyFactor
        fields = GENERAL_FIELDS
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
            'policies': FilteredSelectMultiple(_('policies'), False)
        }
