"""Account selection stage API views."""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.account_selection.models import AccountSelectionStage, AccountSwitchStage


class AccountSelectionStageSerializer(StageSerializer):
    """AccountSelectionStage serializer."""

    class Meta:
        model = AccountSelectionStage
        fields = StageSerializer.Meta.fields


class AccountSelectionStageViewSet(UsedByMixin, ModelViewSet[AccountSelectionStage]):
    """AccountSelectionStage viewset."""

    queryset = AccountSelectionStage.objects.all()
    serializer_class = AccountSelectionStageSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


class AccountSwitchStageSerializer(StageSerializer):
    """AccountSwitchStage serializer."""

    class Meta:
        model = AccountSwitchStage
        fields = StageSerializer.Meta.fields


class AccountSwitchStageViewSet(UsedByMixin, ModelViewSet[AccountSwitchStage]):
    """AccountSwitchStage viewset."""

    queryset = AccountSwitchStage.objects.all()
    serializer_class = AccountSwitchStageSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]
