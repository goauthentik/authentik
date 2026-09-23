from django.db.models import Prefetch
from rest_framework.fields import CharField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, ModelSerializer, PassiveSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.api.request_rules import RequestRuleSerializer
from authentik.enterprise.requests.models import RequestRuleBinding
from authentik.policies.models import PolicyBindingModel


class RelatedTargetSerializer(MetaNameSerializer, PassiveSerializer):
    """Simplified related target object"""

    pbm_uuid = CharField(source="pk", read_only=True)
    label = CharField(source="requestable_label", read_only=True)


class RequestRuleBindingSerializer(EnterpriseRequiredMixin, ModelSerializer):

    rule_obj = RequestRuleSerializer(source="rule", read_only=True)
    related_obj = RelatedTargetSerializer(source="related", many=True, read_only=True)

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
            "related_obj",
            "expiry_pending",
            "expiry_granted_max",
        ]


class RequestRuleBindingViewSet(UsedByMixin, ModelViewSet):

    queryset = RequestRuleBinding.objects.all().prefetch_related(
        Prefetch("related", PolicyBindingModel.objects.select_subclasses())
    )
    serializer_class = RequestRuleBindingSerializer
    filterset_fields = ["rule", "target"]
    search_fields = ["rule__name"]
    ordering = ["rule__name"]
