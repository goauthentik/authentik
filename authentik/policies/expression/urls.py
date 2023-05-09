"""API URLs"""
from authentik.policies.expression.api import ExpressionPolicyViewSet

api_urlpatterns = [("policies/expression", ExpressionPolicyViewSet)]
