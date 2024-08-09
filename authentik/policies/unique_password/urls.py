"""API URLs"""

from authentik.policies.unique_password.api import UniquePasswordPolicyViewSet

api_urlpatterns = [
    ("policies/unique-password", UniquePasswordPolicyViewSet),
]
