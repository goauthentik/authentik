"""API URLs"""
from django.urls import path

from authentik.admin.api.meta import AppsViewSet, ModelViewSet
from authentik.admin.api.metrics import AdministrationMetricsViewSet
from authentik.admin.api.system import SystemView
from authentik.admin.api.tasks import TaskViewSet
from authentik.admin.api.version import VersionView
from authentik.admin.api.workers import WorkerView

api_urlpatterns = [
    ("admin/system_tasks", TaskViewSet, "admin_system_tasks"),
    ("admin/apps", AppsViewSet, "apps"),
    ("admin/models", ModelViewSet, "models"),
    path(
        "admin/metrics/",
        AdministrationMetricsViewSet.as_view(),
        name="admin_metrics",
    ),
    path("admin/version/", VersionView.as_view(), name="admin_version"),
    path("admin/workers/", WorkerView.as_view(), name="admin_workers"),
    path("admin/system/", SystemView.as_view(), name="admin_system"),
]
