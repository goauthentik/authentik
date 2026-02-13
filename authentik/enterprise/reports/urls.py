"""API URLs"""

from authentik.enterprise.reports.api.reports import DataExportViewSet

api_urlpatterns = [
    ("reports/exports", DataExportViewSet),
]
