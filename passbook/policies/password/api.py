"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.policies.forms import GENERAL_SERIALIZER_FIELDS
from passbook.policies.password.models import PasswordPolicy


class PasswordPolicySerializer(ModelSerializer):
    """Password Policy Serializer"""

    class Meta:
        model = PasswordPolicy
        fields = GENERAL_SERIALIZER_FIELDS + [
            "amount_uppercase",
            "amount_lowercase",
            "amount_symbols",
            "length_min",
            "symbol_charset",
            "error_message",
        ]


class PasswordPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = PasswordPolicy.objects.all()
    serializer_class = PasswordPolicySerializer
