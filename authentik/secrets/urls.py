"""Managed secrets API URLs."""

from authentik.secrets.api import SecretViewSet

api_urlpatterns = [("secrets/secrets", SecretViewSet)]
