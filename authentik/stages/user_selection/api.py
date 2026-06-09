"""User selection stage API views."""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.user_selection.models import UserSelectionStage


class UserSelectionStageSerializer(StageSerializer):
    """UserSelectionStage serializer."""

    class Meta:
        model = UserSelectionStage
        fields = StageSerializer.Meta.fields


class UserSelectionStageViewSet(UsedByMixin, ModelViewSet[UserSelectionStage]):
    """UserSelectionStage viewset."""

    queryset = UserSelectionStage.objects.all()
    serializer_class = UserSelectionStageSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]
