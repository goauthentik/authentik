"""Expression Policy API"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.expression.models import ExpressionPolicy


class ExpressionPolicySerializer(PolicySerializer):
    """Group Membership Policy Serializer"""

    class Meta:
        model = ExpressionPolicy
        fields = PolicySerializer.Meta.fields + ["expression"]


class ExpressionPolicyViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = ExpressionPolicy.objects.all()
    serializer_class = ExpressionPolicySerializer
