"""passbook reputation request forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.reputation.models import ReputationPolicy


class ReputationPolicyForm(forms.ModelForm):
    """Form to edit ReputationPolicy"""

    class Meta:

        model = ReputationPolicy
        fields = GENERAL_FIELDS + ["check_ip", "check_username", "threshold"]
        widgets = {
            "name": forms.TextInput(),
            "value": forms.TextInput(),
        }
        labels = {
            "check_ip": _("Check IP"),
        }
