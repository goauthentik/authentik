"""API URLs"""

from authentik.enterprise.policies.unique_password.api import UniquePasswordPolicyViewSet

api_urlpatterns = [
    ("policies/unique_password", UniquePasswordPolicyViewSet),
]
