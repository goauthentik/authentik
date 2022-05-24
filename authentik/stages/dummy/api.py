"""DummyStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.dummy.models import DummyStage


class DummyStageSerializer(StageSerializer):
    """DummyStage Serializer"""

    class Meta:

        model = DummyStage
        fields = StageSerializer.Meta.fields


class DummyStageViewSet(UsedByMixin, ModelViewSet):
    """DummyStage Viewset"""

    queryset = DummyStage.objects.all()
    serializer_class = DummyStageSerializer
    filterset_fields = "__all__"
    search_fields = ["name"]
    ordering = ["name"]
