"""Dummy Policy API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.dummy.models import DummyPolicy
from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS


class DummyPolicySerializer(ModelSerializer):
    """Dummy Policy Serializer"""

    class Meta:
        model = DummyPolicy
        fields = GENERAL_SERIALIZER_FIELDS + ["result", "wait_min", "wait_max"]


class DummyPolicyViewSet(ModelViewSet):
    """Dummy Viewset"""

    queryset = DummyPolicy.objects.all()
    serializer_class = DummyPolicySerializer
