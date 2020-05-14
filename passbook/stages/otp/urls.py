"""passbook OTP Urls"""

from django.urls import path

from passbook.stages.otp import views

urlpatterns = [
    path("", views.UserSettingsView.as_view(), name="otp-user-settings"),
    path("qr/", views.QRView.as_view(), name="otp-qr"),
    path("enable/", views.EnableView.as_view(), name="otp-enable"),
    path("disable/", views.DisableView.as_view(), name="otp-disable"),
]
