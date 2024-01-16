"""API URLs"""
from django.urls import path
from authentik.lib.config import CONFIG

from authentik.tenants.api.tenants import TenantViewSet
from authentik.tenants.api.domains import DomainViewSet
from authentik.tenants.api.settings import SettingsView

api_urlpatterns = [
    path("admin/settings/", SettingsView.as_view(), name="tenant_settings"),
]

if CONFIG.get_bool("tenants.enabled", True):
    api_urlpatterns += [
        ("tenants/tenants", TenantViewSet),
        ("tenants/domains", DomainViewSet),
    ]
