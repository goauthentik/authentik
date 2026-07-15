from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import Application
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.pam.models import PolicyBindingModelRequestRule
from authentik.policies.models import PolicyBindingModel


class PolicyBindingModelRequestRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):

    def validate_pbm(self, pbm: PolicyBindingModel) -> PolicyBindingModel:
        concrete = PolicyBindingModel.objects.filter(pk=pbm.pk).select_subclasses().first()
        if not isinstance(concrete, Application):
            raise ValidationError("Must be an Application")
        return pbm

    class Meta:
        model = PolicyBindingModelRequestRule
        fields = [
            "uuid",
            "policy_engine_mode",
            "name",
            "min_reviewers",
            "min_reviewers_is_per_group",
            "pbm",
            "reviewer_groups",
            "reviewers",
            "notification_transports",
            "notification_mode",
        ]


class PolicyBindingModelRequestRuleViewSet(UsedByMixin, ModelViewSet):
    """Policy-binding request rules"""

    queryset = PolicyBindingModelRequestRule.objects.all()
    serializer_class = PolicyBindingModelRequestRuleSerializer
    filterset_fields = ["pbm__pbm_uuid", "name"]
