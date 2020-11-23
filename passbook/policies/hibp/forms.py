"""passbook HaveIBeenPwned Policy forms"""

from django import forms

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.hibp.models import HaveIBeenPwendPolicy


class HaveIBeenPwnedPolicyForm(forms.ModelForm):
    """Edit HaveIBeenPwendPolicy instances"""

    class Meta:

        model = HaveIBeenPwendPolicy
        fields = GENERAL_FIELDS + ["password_field", "allowed_count"]
        widgets = {
            "name": forms.TextInput(),
            "password_field": forms.TextInput(),
        }
