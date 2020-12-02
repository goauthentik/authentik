"""Expression Policy API"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.forms import GENERAL_SERIALIZER_FIELDS


class ExpressionPolicySerializer(ModelSerializer):
    """Group Membership Policy Serializer"""

    class Meta:
        model = ExpressionPolicy
        fields = GENERAL_SERIALIZER_FIELDS + ["expression"]


class ExpressionPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = ExpressionPolicy.objects.all()
    serializer_class = ExpressionPolicySerializer
