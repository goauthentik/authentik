from typing import Any

from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.models import RequestRule


class RequestRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request_flow = attrs.get("request_flow")
        request = self.context.get("request")
        if not request:
            return attrs
        brand_request_flow = request.brand.flow_request
        if not request_flow and not brand_request_flow:
            raise ValidationError(
                _("A request flow must either be set on this rule, or on the brand.")
            )
        return attrs

    class Meta:
        model = RequestRule
        fields = [
            "uuid",
            "pbm_uuid",
            "policy_engine_mode",
            "name",
            "targets",
            "notification_transports",
            "notification_mode",
            "min_reviewers",
            "min_reviewers_is_per_group",
            "request_flow",
        ]


class RequestRuleViewSet(UsedByMixin, ModelViewSet):

    queryset = RequestRule.objects.all()
    serializer_class = RequestRuleSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name", "pbm_uuid", "request_flow__slug"]
