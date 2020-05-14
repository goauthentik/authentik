"""DummyStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.dummy.models import DummyStage


class DummyStageSerializer(ModelSerializer):
    """DummyStage Serializer"""

    class Meta:

        model = DummyStage
        fields = ["pk", "name"]


class DummyStageViewSet(ModelViewSet):
    """DummyStage Viewset"""

    queryset = DummyStage.objects.all()
    serializer_class = DummyStageSerializer
