"""OTP static urls"""
from django.urls import path

from authentik.stages.otp_static.views import DisableView, UserSettingsView

urlpatterns = [
    path(
        "<uuid:stage_uuid>/settings/", UserSettingsView.as_view(), name="user-settings"
    ),
    path("<uuid:stage_uuid>/disable/", DisableView.as_view(), name="disable"),
]
