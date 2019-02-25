"""passbook HaveIBeenPwned Policy forms"""

from django import forms

from passbook.core.forms.policies import GENERAL_FIELDS
from passbook.hibp_policy.models import HaveIBeenPwendPolicy


class HaveIBeenPwnedPolicyForm(forms.ModelForm):
    """Edit HaveIBeenPwendPolicy instances"""

    class Meta:

        model = HaveIBeenPwendPolicy
        fields = GENERAL_FIELDS + ['allowed_count']
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
        }
