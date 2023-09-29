"""Expression Policy API"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.expression.models import ExpressionPolicy, ExpressionVariable


class ExpressionVariableSerializer(ModelSerializer):
    """Expression Variable Serializer"""

    class Meta:
        model = ExpressionVariable
        fields = "__all__"
        extra_kwargs = {
            "managed": {"read_only": True},
        }


class ExpressionVariableViewSet(UsedByMixin, ModelViewSet):
    """Expression Variable Viewset"""

    queryset = ExpressionVariable.objects.all()
    serializer_class = ExpressionVariableSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class ExpressionPolicySerializer(PolicySerializer):
    """Group Membership Policy Serializer"""

    def validate_expression(self, expr: str) -> str:
        """validate the syntax of the expression"""
        name = "temp-policy" if not self.instance else self.instance.name
        PolicyEvaluator(name).validate(expr)
        return expr

    class Meta:
        model = ExpressionPolicy
        fields = PolicySerializer.Meta.fields + ["expression", "variables"]


class ExpressionPolicyViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = ExpressionPolicy.objects.all()
    serializer_class = ExpressionPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
