from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.models import RequestRule


class RequestRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):

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
