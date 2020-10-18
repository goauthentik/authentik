"""passbook URL Configuration"""
from django.urls import path

from passbook.core.views import impersonate, overview, user

urlpatterns = [
    # User views
    path("-/user/", user.UserSettingsView.as_view(), name="user-settings"),
    path("-/user/tokens/", user.TokenListView.as_view(), name="user-tokens"),
    path(
        "-/user/tokens/create/",
        user.TokenCreateView.as_view(),
        name="user-tokens-create",
    ),
    path(
        "-/user/tokens/<slug:identifier>/update/",
        user.TokenUpdateView.as_view(),
        name="user-tokens-update",
    ),
    path(
        "-/user/tokens/<slug:identifier>/delete/",
        user.TokenDeleteView.as_view(),
        name="user-tokens-delete",
    ),
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
