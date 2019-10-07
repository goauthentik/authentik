"""passbook Policy forms"""

from django import forms

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.group.models import GroupMembershipPolicy


class GroupMembershipPolicyForm(forms.ModelForm):
    """GroupMembershipPolicy Form"""

    class Meta:

        model = GroupMembershipPolicy
        fields = GENERAL_FIELDS + ['group', ]
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
        }
