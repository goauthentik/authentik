"""Source API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.hibp.models import HaveIBeenPwendPolicy


class HaveIBeenPwendPolicySerializer(PolicySerializer):
    """Have I Been Pwned Policy Serializer"""

    class Meta:
        model = HaveIBeenPwendPolicy
        fields = PolicySerializer.Meta.fields + ["password_field", "allowed_count"]


class HaveIBeenPwendPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = HaveIBeenPwendPolicy.objects.all()
    serializer_class = HaveIBeenPwendPolicySerializer
