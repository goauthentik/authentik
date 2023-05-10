"""API URLs"""
from authentik.tenants.api import TenantViewSet

api_urlpatterns = [
    ("core/tenants", TenantViewSet),
]
