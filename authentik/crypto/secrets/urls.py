"""Managed secrets API URLs."""

from authentik.crypto.secrets.api import SecretViewSet

api_urlpatterns = [("secrets/secrets", SecretViewSet)]
