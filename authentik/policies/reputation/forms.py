"""authentik reputation request forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.policies.forms import PolicyForm
from authentik.policies.reputation.models import ReputationPolicy


class ReputationPolicyForm(PolicyForm):
    """Form to edit ReputationPolicy"""

    class Meta:

        model = ReputationPolicy
        fields = PolicyForm.Meta.fields + ["check_ip", "check_username", "threshold"]
        widgets = {
            "name": forms.TextInput(),
            "value": forms.TextInput(),
        }
        labels = {
            "check_ip": _("Check IP"),
        }
