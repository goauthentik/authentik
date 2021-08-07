"""Source API Views"""
from rest_framework import mixins
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.reputation.models import IPReputation, ReputationPolicy, UserReputation


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
    ordering = ["name"]


class IPReputationSerializer(ModelSerializer):
    """IPReputation Serializer"""

    class Meta:
        model = IPReputation
        fields = [
            "pk",
            "ip",
            "score",
            "updated",
        ]


class IPReputationViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """IPReputation Viewset"""

    queryset = IPReputation.objects.all()
    serializer_class = IPReputationSerializer
    search_fields = ["ip", "score"]
    filterset_fields = ["ip", "score"]
    ordering = ["ip"]


class UserReputationSerializer(ModelSerializer):
    """UserReputation Serializer"""

    class Meta:
        model = UserReputation
        fields = [
            "pk",
            "username",
            "score",
            "updated",
        ]


class UserReputationViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """UserReputation Viewset"""

    queryset = UserReputation.objects.all()
    serializer_class = UserReputationSerializer
    search_fields = ["username", "score"]
    filterset_fields = ["username", "score"]
    ordering = ["username"]
