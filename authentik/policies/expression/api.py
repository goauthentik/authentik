"""Expression Policy API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.expression.models import ExpressionPolicy


class ExpressionPolicySerializer(PolicySerializer):
    """Group Membership Policy Serializer"""

    def validate_expression(self, expr: str) -> str:
        """validate the syntax of the expression"""
        name = "temp-policy" if not self.instance else self.instance.name
        request = self.context.get("request")
        PolicyEvaluator(request.user if request else None, name).validate(expr)
        return expr

    class Meta:
        model = ExpressionPolicy
        fields = PolicySerializer.Meta.fields + ["expression", "execution_user"]


class ExpressionPolicyViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = ExpressionPolicy.objects.all()
    serializer_class = ExpressionPolicySerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
