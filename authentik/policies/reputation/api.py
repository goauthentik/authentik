"""Source API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.reputation.models import (
    IPReputation,
    ReputationPolicy,
    UserReputation,
)


class ReputationPolicySerializer(PolicySerializer):
    """Reputation Policy Serializer"""

    class Meta:
        model = ReputationPolicy
        fields = PolicySerializer.Meta.fields + [
            "check_ip",
            "check_username",
            "threshold",
        ]


class ReputationPolicyViewSet(ModelViewSet):
    """Reputation Policy Viewset"""

    queryset = ReputationPolicy.objects.all()
    serializer_class = ReputationPolicySerializer


class IPReputationSerializer(PolicySerializer):
    """IPReputation Serializer"""

    class Meta:
        model = IPReputation
        fields = [
            "pk",
            "ip",
            "score",
            "updated",
        ]


class IPReputationViewSet(ModelViewSet):
    """IPReputation Viewset"""

    queryset = IPReputation.objects.all()
    serializer_class = IPReputationSerializer


class UserReputationSerializer(PolicySerializer):
    """UserReputation Serializer"""

    class Meta:
        model = UserReputation
        fields = [
            "pk",
            "user",
            "score",
            "updated",
        ]


class UserReputationViewSet(ModelViewSet):
    """UserReputation Viewset"""

    queryset = UserReputation.objects.all()
    serializer_class = UserReputationSerializer
