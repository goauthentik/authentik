from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.pam.api.apps import RequestableTargetSerializer
from authentik.enterprise.pam.models import PolicyBindingModelRequestRule
from authentik.policies.api.bindings import PolicyBindingModelForeignKey
from authentik.policies.models import PolicyBindingModel, RequestableMixin


class PolicyBindingModelRequestRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):

    pbms = PolicyBindingModelForeignKey(
        queryset=PolicyBindingModel.objects.select_subclasses(), many=True
    )

    pbm_targets = SerializerMethodField()

    @extend_schema_field(RequestableTargetSerializer(many=True))
    def get_pbm_targets(
        self, inst: PolicyBindingModelRequestRule
    ) -> list[RequestableTargetSerializer]:
        return RequestableTargetSerializer(inst.pbms.select_subclasses(), many=True).data

    def validate_pbms(self, pbms: list[PolicyBindingModel]) -> list[PolicyBindingModel]:
        for pbm in pbms:
            if not isinstance(pbm, RequestableMixin):
                raise ValidationError(
                    f"'{pbm}' is not a requestable object "
                    "(e.g. an Application or Application Entitlement)"
                )
        return pbms

    class Meta:
        model = PolicyBindingModelRequestRule
        fields = [
            "uuid",
            "pbm_uuid",
            "policy_engine_mode",
            "name",
            "min_reviewers",
            "min_reviewers_is_per_group",
            "pbms",
            "pbm_targets",
            "reviewer_groups",
            "reviewers",
            "notification_transports",
            "notification_mode",
        ]


class PolicyBindingModelRequestRuleViewSet(UsedByMixin, ModelViewSet):
    """Policy-binding request rules"""

    queryset = PolicyBindingModelRequestRule.objects.all()
    serializer_class = PolicyBindingModelRequestRuleSerializer
    filterset_fields = ["pbms__pbm_uuid", "name"]
