"""Dummy Policy API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.dummy.models import DummyPolicy


class DummyPolicySerializer(PolicySerializer):
    """Dummy Policy Serializer"""

    class Meta:
        model = DummyPolicy
        fields = PolicySerializer.Meta.fields + ["result", "wait_min", "wait_max"]


class DummyPolicyViewSet(ModelViewSet):
    """Dummy Viewset"""

    queryset = DummyPolicy.objects.all()
    serializer_class = DummyPolicySerializer
