"""API URLs"""

from authentik.analytics.api import AnalyticsDataViewSet, AnalyticsDescriptionViewSet

api_urlpatterns = [
    ("analytics/description", AnalyticsDescriptionViewSet, "analytics-description"),
    ("analytics/data", AnalyticsDataViewSet, "analytics-data"),
]
