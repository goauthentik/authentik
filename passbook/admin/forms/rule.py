"""passbook administration forms"""
from django import forms

from passbook.core.models import User


class RuleTestForm(forms.Form):
    """Form to test rule against user"""

    user = forms.ModelChoiceField(queryset=User.objects.all())
