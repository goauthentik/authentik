"""API URLs"""

from authentik.policies.password.api import PasswordPolicyViewSet, UniquePasswordPolicyViewSet

api_urlpatterns = [
    ("policies/password", PasswordPolicyViewSet),
    ("policies/unique-password", UniquePasswordPolicyViewSet),
]
