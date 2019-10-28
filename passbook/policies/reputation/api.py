"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.reputation.models import ReputationPolicy


class ReputationPolicySerializer(ModelSerializer):
    """Reputation Policy Serializer"""

    class Meta:
        model = ReputationPolicy
        fields = GENERAL_SERIALIZER_FIELDS + ['check_ip', 'check_username', 'threshold']


class ReputationPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = ReputationPolicy.objects.all()
    serializer_class = ReputationPolicySerializer
