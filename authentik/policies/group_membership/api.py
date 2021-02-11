"""Group Membership Policy API"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.group_membership.models import GroupMembershipPolicy


class GroupMembershipPolicySerializer(PolicySerializer):
    """Group Membership Policy Serializer"""

    class Meta:
        model = GroupMembershipPolicy
        fields = PolicySerializer.Meta.fields + [
            "group",
        ]


class GroupMembershipPolicyViewSet(ModelViewSet):
    """Group Membership Policy Viewset"""

    queryset = GroupMembershipPolicy.objects.all()
    serializer_class = GroupMembershipPolicySerializer
