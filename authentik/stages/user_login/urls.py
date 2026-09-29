"""API URLs"""

from django.urls import path

from authentik.stages.user_login.api import UserLoginStageViewSet
from authentik.stages.user_login.views import (
    DeviceBoundSessionCredentailsStart,
    DeviceBoundSessionCredentialRefresh,
)

api_urlpatterns = [
    ("stages/user_login", UserLoginStageViewSet),
    path(
        "dbsc/start/",
        DeviceBoundSessionCredentailsStart.as_view(),
        name="dbsc-start",
    ),
    path(
        "dbsc/refresh/",
        DeviceBoundSessionCredentialRefresh.as_view(),
        name="dbsc-refresh",
    ),
]
