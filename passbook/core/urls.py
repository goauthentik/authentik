"""passbook URL Configuration"""
from django.urls import path

from passbook.core.views import impersonate, overview, user

urlpatterns = [
    # User views
    path("-/user/", user.UserSettingsView.as_view(), name="user-settings"),
    # Overview
    path("", overview.OverviewView.as_view(), name="overview"),
    # Impersonation
    path(
        "-/impersonation/<int:user_id>/",
        impersonate.ImpersonateInitView.as_view(),
        name="impersonate-init",
    ),
    path(
        "-/impersonation/end/",
        impersonate.ImpersonateEndView.as_view(),
        name="impersonate-end",
    ),
]
