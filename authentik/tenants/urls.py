"""API URLs"""

from django.conf import settings
from django.urls import path

from authentik.common.config import CONFIG
from authentik.tenants.api.domains import DomainViewSet
from authentik.tenants.api.settings import SettingsView
from authentik.tenants.api.tenants import TenantViewSet

api_urlpatterns = [
    path("admin/settings/", SettingsView.as_view(), name="tenant_settings"),
]

if CONFIG.get_bool("tenants.enabled", True) or settings.TEST:
    api_urlpatterns += [
        ("tenants/tenants", TenantViewSet),
        ("tenants/domains", DomainViewSet),
    ]
