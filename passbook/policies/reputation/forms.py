"""passbook reputation request forms"""
from django import forms

from passbook.core.forms.policies import GENERAL_FIELDS
from passbook.policies.reputation.models import ReputationPolicy


class ReputationPolicyForm(forms.ModelForm):
    """Form to edit ReputationPolicy"""

    class Meta:

        model = ReputationPolicy
        fields = GENERAL_FIELDS + ['check_ip', 'check_username', 'threshold']
        widgets = {
            'name': forms.TextInput(),
            'value': forms.TextInput(),
        }
