"""Group Membership Policy API"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.group_membership.models import GroupMembershipPolicy


class GroupMembershipPolicySerializer(ModelSerializer):
    """Group Membership Policy Serializer"""

    class Meta:
        model = GroupMembershipPolicy
        fields = GENERAL_SERIALIZER_FIELDS + [
            "group",
        ]


class GroupMembershipPolicyViewSet(ModelViewSet):
    """Group Membership Policy Viewset"""

    queryset = GroupMembershipPolicy.objects.all()
    serializer_class = GroupMembershipPolicySerializer
