from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.api.request_rules import RequestRuleSerializer
from authentik.enterprise.requests.models import RequestRuleBinding


class RequestRuleBindingSerializer(EnterpriseRequiredMixin, ModelSerializer):

    rule_obj = RequestRuleSerializer(source="rule", read_only=True)

    class Meta:
        model = RequestRuleBinding
        fields = [
            "uuid",
            "pbm_uuid",
            "policy_engine_mode",
            "rule",
            "rule_obj",
            "target",
            "related",
        ]


class RequestRuleBindingViewSet(UsedByMixin, ModelViewSet):

    queryset = RequestRuleBinding.objects.all()
    serializer_class = RequestRuleBindingSerializer
    filterset_fields = ["rule", "target"]
    search_fields = ["rule__name"]
    ordering = ["rule__name"]
