"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.policies.forms import GENERAL_SERIALIZER_FIELDS
from authentik.policies.hibp.models import HaveIBeenPwendPolicy


class HaveIBeenPwendPolicySerializer(ModelSerializer):
    """Have I Been Pwned Policy Serializer"""

    class Meta:
        model = HaveIBeenPwendPolicy
        fields = GENERAL_SERIALIZER_FIELDS + ["password_field", "allowed_count"]


class HaveIBeenPwendPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = HaveIBeenPwendPolicy.objects.all()
    serializer_class = HaveIBeenPwendPolicySerializer
