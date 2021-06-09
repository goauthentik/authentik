"""DummyStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.dummy.models import DummyStage


class DummyStageSerializer(StageSerializer):
    """DummyStage Serializer"""

    class Meta:

        model = DummyStage
        fields = StageSerializer.Meta.fields


from authentik.core.api.used_by import UsedByMixin


class DummyStageViewSet(UsedByMixin, ModelViewSet):
    """DummyStage Viewset"""

    queryset = DummyStage.objects.all()
    serializer_class = DummyStageSerializer
