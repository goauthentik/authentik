"""authentik URL Configuration"""
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView

from authentik.core.views import impersonate, shell, user
from authentik.flows.views import FlowExecutorShellView

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="authentik_core:if-admin"),
        name="root-redirect",
    ),
    # User views
    path("-/user/details/", user.UserDetailsView.as_view(), name="user-details"),
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
    path(
        "if/flow/<slug:flow_slug>/",
        ensure_csrf_cookie(FlowExecutorShellView.as_view()),
        name="if-flow",
    ),
    path("if/admin/", ensure_csrf_cookie(shell.ShellView.as_view()), name="if-admin"),
]
