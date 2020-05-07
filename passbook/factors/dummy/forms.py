"""passbook administration forms"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.factors.dummy.models import DummyFactor
from passbook.flows.forms import GENERAL_FIELDS


class DummyFactorForm(forms.ModelForm):
    """Form to create/edit Dummy Factor"""

    class Meta:

        model = DummyFactor
        fields = GENERAL_FIELDS
        widgets = {
            "name": forms.TextInput(),
            "order": forms.NumberInput(),
            "policies": FilteredSelectMultiple(_("policies"), False),
        }
