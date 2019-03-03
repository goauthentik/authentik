"""passbook PasswordExpiry Policy forms"""

from django import forms
from django.utils.translation import gettext as _

from passbook.core.forms.policies import GENERAL_FIELDS
from passbook.password_expiry_policy.models import PasswordExpiryPolicy


class PasswordExpiryPolicyForm(forms.ModelForm):
    """Edit PasswordExpiryPolicy instances"""

    class Meta:

        model = PasswordExpiryPolicy
        fields = GENERAL_FIELDS + ['days', 'deny_only']
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
            'days': forms.NumberInput(),
        }
        labels = {
            'deny_only': _("Only fail the policy, don't set user's password.")
        }
