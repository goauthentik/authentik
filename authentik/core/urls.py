"""authentik URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

from authentik.core.views import impersonate, user
from authentik.flows.views import FlowExecutorShellView

urlpatterns = [
    path(
        "",
        login_required(RedirectView.as_view(pattern_name="authentik_core:if-admin")),
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
    # Interfaces
    path(
        "if/admin/",
        ensure_csrf_cookie(TemplateView.as_view(template_name="shell.html")),
        name="if-admin",
    ),
    path(
        "if/flow/<slug:flow_slug>/",
        ensure_csrf_cookie(FlowExecutorShellView.as_view()),
        name="if-flow",
    ),
]
