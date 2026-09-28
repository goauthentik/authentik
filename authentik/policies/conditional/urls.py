"""API URLs"""

from authentik.policies.conditional.api import ConditionalPolicyViewSet

api_urlpatterns = [("policies/conditional", ConditionalPolicyViewSet)]
