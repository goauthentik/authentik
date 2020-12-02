"""authentik Group Membership Policy forms"""

from django import forms

from authentik.policies.forms import GENERAL_FIELDS
from authentik.policies.group_membership.models import GroupMembershipPolicy


class GroupMembershipPolicyForm(forms.ModelForm):
    """GroupMembershipPolicy Form"""

    class Meta:

        model = GroupMembershipPolicy
        fields = GENERAL_FIELDS + [
            "group",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
