from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.requests.models import RequestRule


class RequestRuleSerializer(ModelSerializer):

    class Meta:
        model = RequestRule
        fields = [
            "uuid",
            "pbm_uuid",
            "policy_engine_mode",
            "name",
            "targets",
        ]


class RequestRuleViewSet(UsedByMixin, ModelViewSet):

    queryset = RequestRule.objects.all()
    serializer_class = RequestRuleSerializer
    search_fields = ["name"]
