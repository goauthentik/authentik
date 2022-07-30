"""Source API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.hibp.models import HaveIBeenPwendPolicy


class HaveIBeenPwendPolicySerializer(PolicySerializer):
    """Have I Been Pwned Policy Serializer"""

    class Meta:
        model = HaveIBeenPwendPolicy
        fields = PolicySerializer.Meta.fields + ["password_field", "allowed_count"]


class HaveIBeenPwendPolicyViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = HaveIBeenPwendPolicy.objects.all()
    serializer_class = HaveIBeenPwendPolicySerializer
    filterset_fields = "__all__"
    search_fields = ["name", "password_field"]
    ordering = ["name"]
