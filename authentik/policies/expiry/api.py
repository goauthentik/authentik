"""Password Expiry Policy API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.expiry.models import PasswordExpiryPolicy


class PasswordExpiryPolicySerializer(PolicySerializer):
    """Password Expiry Policy Serializer"""

    class Meta:
        model = PasswordExpiryPolicy
        fields = PolicySerializer.Meta.fields + ["days", "deny_only"]


class PasswordExpiryPolicyViewSet(UsedByMixin, ModelViewSet):
    """Password Expiry Viewset"""

    queryset = PasswordExpiryPolicy.objects.all()
    serializer_class = PasswordExpiryPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
