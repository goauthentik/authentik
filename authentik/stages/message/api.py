"""MessageStage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.message.models import MessageStage


class MessageStageSerializer(StageSerializer):
    """MessageStage Serializer"""

    class Meta:
        model = MessageStage
        fields = StageSerializer.Meta.fields + ["title", "message", "button_text"]


class MessageStageViewSet(UsedByMixin, ModelViewSet[MessageStage]):
    """MessageStage Viewset"""

    queryset = MessageStage.objects.all()
    serializer_class = MessageStageSerializer
    filterset_fields = "__all__"
    search_fields = ["name", "title", "message", "button_text"]
    ordering = ["name"]
