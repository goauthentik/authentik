"""RedirectStage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.redirect.models import RedirectStage


class RedirectStageSerializer(StageSerializer):
    """RedirectStage Serializer"""

    class Meta:
        model = RedirectStage
        fields = StageSerializer.Meta.fields + [
            "keep_context",
            "redirect_to_flow",
        ]


class RedirectStageViewSet(UsedByMixin, ModelViewSet):
    """RedirectStage Viewset"""

    queryset = RedirectStage.objects.all()
    serializer_class = RedirectStageSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]
