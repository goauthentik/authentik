"""flow urls"""
from django.urls import path

from passbook.flows.view import AuthenticationView, FactorPermissionDeniedView

urlpatterns = [
    path("auth/process/", AuthenticationView.as_view(), name="auth-process"),
    path(
        "auth/process/<slug:factor>/",
        AuthenticationView.as_view(),
        name="auth-process",
    ),
    path(
        "auth/process/denied/",
        FactorPermissionDeniedView.as_view(),
        name="auth-denied",
    ),
]
