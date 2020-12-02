"""Password stage urls"""
from django.urls import path

from authentik.stages.password.views import UserSettingsCardView

urlpatterns = [
    path(
        "<uuid:stage_uuid>/change-card/",
        UserSettingsCardView.as_view(),
        name="user-settings",
    ),
]
