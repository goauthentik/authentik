"""API URLs"""
from django.urls import path

from authentik.lib.config import CONFIG
from authentik.tenants.api import SettingsView, TenantViewSet

api_urlpatterns = [
    path("admin/settings/", SettingsView.as_view(), name="tenant_settings"),
]

if CONFIG.get_bool("tenants.api.enabled", False):
    api_urlpatterns += [
        (
            "tenants",
            TenantViewSet,
        ),
    ]
