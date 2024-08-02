"""API URLs"""

from authentik.policies.password.api import UniquePasswordPolicyViewSet

api_urlpatterns = [
    ("policies/unique-password", UniquePasswordPolicyViewSet),
]
