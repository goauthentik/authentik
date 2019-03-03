"""passbook suspicious request forms"""
from django import forms

from passbook.core.forms.policies import GENERAL_FIELDS
from passbook.suspicious_policy.models import SuspiciousRequestPolicy


class SuspiciousRequestPolicyForm(forms.ModelForm):
    """Form to edit SuspiciousRequestPolicy"""

    class Meta:

        model = SuspiciousRequestPolicy
        fields = GENERAL_FIELDS + ['check_ip', 'check_username', 'threshold']
        widgets = {
            'name': forms.TextInput(),
            'value': forms.TextInput(),
        }
