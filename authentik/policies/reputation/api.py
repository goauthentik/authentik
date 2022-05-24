"""Reputation policy API Views"""
from rest_framework import mixins
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.reputation.models import Reputation, ReputationPolicy


class ReputationPolicySerializer(PolicySerializer):
    """Reputation Policy Serializer"""

    class Meta:
        model = ReputationPolicy
        fields = PolicySerializer.Meta.fields + [
            "check_ip",
            "check_username",
            "threshold",
        ]


class ReputationPolicyViewSet(UsedByMixin, ModelViewSet):
    """Reputation Policy Viewset"""

    queryset = ReputationPolicy.objects.all()
    serializer_class = ReputationPolicySerializer
    filterset_fields = "__all__"
    search_fields = ["name", "threshold"]
    ordering = ["name"]


class ReputationSerializer(ModelSerializer):
    """Reputation Serializer"""

    class Meta:
        model = Reputation
        fields = [
            "pk",
            "identifier",
            "ip",
            "ip_geo_data",
            "score",
            "updated",
        ]


class ReputationViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Reputation Viewset"""

    queryset = Reputation.objects.all()
    serializer_class = ReputationSerializer
    search_fields = ["identifier", "ip", "score"]
    filterset_fields = ["identifier", "ip", "score"]
    ordering = ["ip"]
