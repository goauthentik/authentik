"""Flow Binding API Views"""
from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.flows.models import FlowStageBinding


class FlowStageBindingSerializer(ModelSerializer):
    """FlowStageBinding Serializer"""

    stage_obj = StageSerializer(read_only=True, source="stage")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        evaluate_on_plan = attrs.get("evaluate_on_plan", False)
        re_evaluate_policies = attrs.get("re_evaluate_policies", True)
        if not evaluate_on_plan and not re_evaluate_policies:
            raise ValidationError("Either evaluation on plan or evaluation on run must be enabled")
        return super().validate(attrs)

    class Meta:
        model = FlowStageBinding
        fields = [
            "pk",
            "policybindingmodel_ptr_id",
            "target",
            "stage",
            "stage_obj",
            "evaluate_on_plan",
            "re_evaluate_policies",
            "order",
            "policy_engine_mode",
            "invalid_response_action",
        ]


class FlowStageBindingViewSet(UsedByMixin, ModelViewSet):
    """FlowStageBinding Viewset"""

    queryset = FlowStageBinding.objects.all()
    serializer_class = FlowStageBindingSerializer
    filterset_fields = "__all__"
    search_fields = ["stage__name"]
    ordering = ["order"]
