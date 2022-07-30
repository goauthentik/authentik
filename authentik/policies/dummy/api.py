"""Dummy Policy API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.dummy.models import DummyPolicy


class DummyPolicySerializer(PolicySerializer):
    """Dummy Policy Serializer"""

    class Meta:
        model = DummyPolicy
        fields = PolicySerializer.Meta.fields + ["result", "wait_min", "wait_max"]


class DummyPolicyViewSet(UsedByMixin, ModelViewSet):
    """Dummy Viewset"""

    queryset = DummyPolicy.objects.all()
    serializer_class = DummyPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
