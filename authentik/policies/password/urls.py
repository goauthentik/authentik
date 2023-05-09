"""API URLs"""
from authentik.policies.password.api import PasswordPolicyViewSet

api_urlpatterns = [("policies/password", PasswordPolicyViewSet)]
