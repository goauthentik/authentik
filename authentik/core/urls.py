"""authentik URL Configuration"""
from django.urls import path

from authentik.core.views import impersonate, library, shell, user

urlpatterns = [
    path("", shell.ShellView.as_view(), name="shell"),
    # User views
    path("-/user/", user.UserSettingsView.as_view(), name="user-settings"),
    path("-/user/details/", user.UserDetailsView.as_view(), name="user-details"),
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
    # Libray
    path("library/", library.LibraryView.as_view(), name="overview"),
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
