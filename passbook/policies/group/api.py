"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.group.models import GroupMembershipPolicy


class GroupMembershipPolicySerializer(ModelSerializer):
    """Group Membership Policy Serializer"""

    class Meta:
        model = GroupMembershipPolicy
        fields = GENERAL_SERIALIZER_FIELDS + ['group']


class GroupMembershipPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = GroupMembershipPolicy.objects.all()
    serializer_class = GroupMembershipPolicySerializer
