"""passbook administration forms"""
from django import forms

from passbook.core.auth.factor_manager import MANAGER
from passbook.core.models import Factor
from passbook.lib.utils.reflection import class_to_path


def get_factors():
    """Return list of factors for Select Widget"""
    for factor in MANAGER.all:
        yield (class_to_path(factor), factor.__name__)

class FactorForm(forms.ModelForm):
    """Form to create/edit Factors"""

    class Meta:

        model = Factor
        fields = ['name', 'slug', 'order', 'policies', 'type', 'enabled', 'arguments']
        widgets = {
            'type': forms.Select(choices=get_factors()),
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
        }
