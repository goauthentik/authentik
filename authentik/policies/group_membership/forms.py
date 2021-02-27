"""authentik Group Membership Policy forms"""

from django import forms

from authentik.core.models import Group
from authentik.policies.forms import GENERAL_FIELDS
from authentik.policies.group_membership.models import GroupMembershipPolicy


class GroupMembershipPolicyForm(forms.ModelForm):
    """GroupMembershipPolicy Form"""

    group = forms.ModelChoiceField(queryset=Group.objects.all().order_by("name"))

    class Meta:

        model = GroupMembershipPolicy
        fields = GENERAL_FIELDS + [
            "group",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
