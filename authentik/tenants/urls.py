"""API URLs"""
from django.urls import path

from authentik.tenants.api import DomainViewSet, SettingsView, TenantViewSet

api_urlpatterns = [
    path("admin/settings/", SettingsView.as_view(), name="tenant_settings"),
    (
        "tenants/tenants",
        TenantViewSet,
    ),
    (
        "tenants/domains",
        DomainViewSet,
    ),
]
