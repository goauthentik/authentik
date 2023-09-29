"""API URLs"""
from authentik.policies.expression.api import ExpressionPolicyViewSet, ExpressionVariableViewSet

api_urlpatterns = [
    ("policies/expression/variables", ExpressionVariableViewSet),
    ("policies/expression", ExpressionPolicyViewSet),
]
