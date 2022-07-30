"""Password Policy API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.password.models import PasswordPolicy


class PasswordPolicySerializer(PolicySerializer):
    """Password Policy Serializer"""

    class Meta:
        model = PasswordPolicy
        fields = PolicySerializer.Meta.fields + [
            "password_field",
            "amount_digits",
            "amount_uppercase",
            "amount_lowercase",
            "amount_symbols",
            "length_min",
            "symbol_charset",
            "error_message",
        ]


class PasswordPolicyViewSet(UsedByMixin, ModelViewSet):
    """Password Policy Viewset"""

    queryset = PasswordPolicy.objects.all()
    serializer_class = PasswordPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
