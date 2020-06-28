from django.urls import path

from passbook.stages.otp_time.views import UserSettingsView, DisableView

urlpatterns = [
    path("settings", UserSettingsView.as_view(), name="user-settings"),
    path("disable", DisableView.as_view(), name="disable")
]
