"""DummyFactor API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.factors.dummy.models import DummyFactor


class DummyFactorSerializer(ModelSerializer):
    """DummyFactor Serializer"""

    class Meta:

        model = DummyFactor
        fields = ["pk", "name", "slug", "order", "enabled"]


class DummyFactorViewSet(ModelViewSet):
    """DummyFactor Viewset"""

    queryset = DummyFactor.objects.all()
    serializer_class = DummyFactorSerializer
