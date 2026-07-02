from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.pam.models import PolicyBindingModelRequestRule


class PolicyBindingModelRequestRuleSerializer(ModelSerializer):

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
        ]


class PolicyBindingModelRequestRuleViewSet(ModelViewSet):

    queryset = PolicyBindingModelRequestRule.objects.all()
    serializer_class = PolicyBindingModelRequestRuleSerializer
    filterset_fields = ["pbm__pbm_uuid", "name"]
