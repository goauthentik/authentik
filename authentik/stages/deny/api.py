"""deny Stage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.deny.models import DenyStage


class DenyStageSerializer(StageSerializer):
    """DenyStage Serializer"""

    class Meta:
        model = DenyStage
        fields = StageSerializer.Meta.fields + ["deny_message"]


class DenyStageViewSet(ModelViewSet):
    """DenyStage Viewset"""

    queryset = DenyStage.objects.all()
    serializer_class = DenyStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
