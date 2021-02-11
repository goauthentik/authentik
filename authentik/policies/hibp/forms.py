"""authentik HaveIBeenPwned Policy forms"""

from django import forms

from authentik.policies.forms import PolicyForm
from authentik.policies.hibp.models import HaveIBeenPwendPolicy


class HaveIBeenPwnedPolicyForm(PolicyForm):
    """Edit HaveIBeenPwendPolicy instances"""

    class Meta:

        model = HaveIBeenPwendPolicy
        fields = PolicyForm.Meta.fields + ["password_field", "allowed_count"]
        widgets = {
            "name": forms.TextInput(),
            "password_field": forms.TextInput(),
        }
