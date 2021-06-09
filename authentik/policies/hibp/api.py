"""Source API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api.policies import PolicySerializer
from authentik.policies.hibp.models import HaveIBeenPwendPolicy


class HaveIBeenPwendPolicySerializer(PolicySerializer):
    """Have I Been Pwned Policy Serializer"""

    class Meta:
        model = HaveIBeenPwendPolicy
        fields = PolicySerializer.Meta.fields + ["password_field", "allowed_count"]


from authentik.core.api.used_by import UsedByMixin


class HaveIBeenPwendPolicyViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = HaveIBeenPwendPolicy.objects.all()
    serializer_class = HaveIBeenPwendPolicySerializer
