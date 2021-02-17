"""DummyStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.dummy.models import DummyStage


class DummyStageSerializer(StageSerializer):
    """DummyStage Serializer"""

    class Meta:

        model = DummyStage
        fields = StageSerializer.Meta.fields


class DummyStageViewSet(ModelViewSet):
    """DummyStage Viewset"""

    queryset = DummyStage.objects.all()
    serializer_class = DummyStageSerializer
