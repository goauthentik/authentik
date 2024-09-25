"""API URLs"""

from authentik.analytics.api import AnalyticsDataViewSet, AnalyticsDescriptionViewSet

api_urlpatterns = [
    ("analytics/description", AnalyticsDescriptionViewSet, "description"),
    ("analytics/data", AnalyticsDataViewSet, "data"),
]
