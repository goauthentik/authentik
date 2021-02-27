"""authentik Group Membership Policy forms"""

from django import forms

from authentik.core.models import Group
from authentik.policies.forms import PolicyForm
from authentik.policies.group_membership.models import GroupMembershipPolicy


class GroupMembershipPolicyForm(PolicyForm):
    """GroupMembershipPolicy Form"""

    group = forms.ModelChoiceField(queryset=Group.objects.all().order_by("name"))

    class Meta:

        model = GroupMembershipPolicy
        fields = PolicyForm.Meta.fields + [
            "group",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
