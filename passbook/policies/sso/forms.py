"""passbook Policy forms"""

from django import forms

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.sso.models import SSOLoginPolicy


class SSOLoginPolicyForm(forms.ModelForm):
    """Edit SSOLoginPolicy instances"""

    class Meta:

        model = SSOLoginPolicy
        fields = GENERAL_FIELDS
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
        }
