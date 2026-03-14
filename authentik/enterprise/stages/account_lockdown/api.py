"""Account Lockdown Stage API Views"""

from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.stages.account_lockdown.models import AccountLockdownStage
from authentik.flows.api.stages import StageSerializer
from authentik.flows.models import FlowAuthenticationRequirement


class AccountLockdownStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """AccountLockdownStage Serializer"""

    def validate_self_service_completion_flow(self, flow):
        if flow and flow.authentication != FlowAuthenticationRequirement.NONE:
            raise ValidationError(
                "Completion flow must not require authentication for self-service lockdown."
            )
        return flow

    class Meta:
        model = AccountLockdownStage
        fields = StageSerializer.Meta.fields + [
            "deactivate_user",
            "set_unusable_password",
            "delete_sessions",
            "revoke_tokens",
            "self_service_message_title",
            "self_service_message",
            "self_service_completion_flow",
        ]


class AccountLockdownStageViewSet(UsedByMixin, ModelViewSet):
    """AccountLockdownStage Viewset"""

    queryset = AccountLockdownStage.objects.all()
    serializer_class = AccountLockdownStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
