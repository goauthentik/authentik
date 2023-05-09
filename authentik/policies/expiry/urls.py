"""API URLs"""
from authentik.policies.expiry.api import PasswordExpiryPolicyViewSet

api_urlpatterns = [("policies/password_expiry", PasswordExpiryPolicyViewSet)]
