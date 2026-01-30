"""Account Lockdown Stage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.flows.api.stages import StageSerializer


class AccountLockdownStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """AccountLockdownStage Serializer"""

    class Meta:
        model = AccountLockdownStage
        fields = StageSerializer.Meta.fields + [
            "deactivate_user",
            "set_unusable_password",
            "delete_sessions",
            "revoke_tokens",
        ]


class AccountLockdownStageViewSet(UsedByMixin, ModelViewSet):
    """AccountLockdownStage Viewset"""

    queryset = AccountLockdownStage.objects.all()
    serializer_class = AccountLockdownStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
