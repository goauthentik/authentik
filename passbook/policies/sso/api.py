"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.sso.models import SSOLoginPolicy


class SSOLoginPolicySerializer(ModelSerializer):
    """SSO Login Policy Serializer"""

    class Meta:
        model = SSOLoginPolicy
        fields = GENERAL_SERIALIZER_FIELDS


class SSOLoginPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = SSOLoginPolicy.objects.all()
    serializer_class = SSOLoginPolicySerializer
