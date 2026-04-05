from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.policies.unique_password.models import UniquePasswordPolicy
from authentik.policies.api.policies import PolicySerializer


class UniquePasswordPolicySerializer(EnterpriseRequiredMixin, PolicySerializer):
    """Password Uniqueness Policy Serializer"""

    class Meta:
        model = UniquePasswordPolicy
        fields = PolicySerializer.Meta.fields + [
            "password_field",
            "num_historical_passwords",
        ]


class UniquePasswordPolicyViewSet(UsedByMixin, ModelViewSet):
    """Password Uniqueness Policy Viewset"""

    queryset = UniquePasswordPolicy.objects.all()
    serializer_class = UniquePasswordPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
