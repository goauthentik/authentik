"""Source API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.reputation.models import ReputationPolicy


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
    """Source Viewset"""

    queryset = ReputationPolicy.objects.all()
    serializer_class = ReputationPolicySerializer
