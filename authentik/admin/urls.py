"""API URLs"""

from django.urls import path

from authentik.admin.api.meta import AppsViewSet, ModelViewSet
from authentik.admin.api.system import SystemView
from authentik.admin.api.version import VersionView
from authentik.admin.api.version_history import VersionHistoryViewSet

api_urlpatterns = [
    ("admin/apps", AppsViewSet, "apps"),
    ("admin/models", ModelViewSet, "models"),
    path("admin/version/", VersionView.as_view(), name="admin_version"),
    ("admin/version/history", VersionHistoryViewSet, "version_history"),
    path("admin/system/", SystemView.as_view(), name="admin_system"),
]
