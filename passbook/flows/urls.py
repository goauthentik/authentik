"""flow urls"""
from django.urls import path

from passbook.flows.views import (
    AuthenticationView,
    FactorPermissionDeniedView,
    FlowExecutorView,
)

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
    path("<slug:flow_slug>/", FlowExecutorView.as_view(), name="flow-executor"),
]
