"""authentik URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

from authentik.core.views import apps, impersonate
from authentik.core.views.interface import FlowInterfaceView
from authentik.core.views.session import EndSessionView

urlpatterns = [
    path(
        "",
        login_required(RedirectView.as_view(pattern_name="authentik_core:if-user")),
        name="root-redirect",
    ),
    path(
        # We have to use this format since everything else uses applications/o or applications/saml
        "application/launch/<slug:application_slug>/",
        apps.RedirectToAppLaunch.as_view(),
        name="application-launch",
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
        ensure_csrf_cookie(TemplateView.as_view(template_name="if/admin.html")),
        name="if-admin",
    ),
    path(
        "if/user/",
        ensure_csrf_cookie(TemplateView.as_view(template_name="if/user.html")),
        name="if-user",
    ),
    path(
        "if/flow/<slug:flow_slug>/",
        ensure_csrf_cookie(FlowInterfaceView.as_view()),
        name="if-flow",
    ),
    path(
        "if/session-end/<slug:application_slug>/",
        ensure_csrf_cookie(EndSessionView.as_view()),
        name="if-session-end",
    ),
    # Fallback for WS
    path("ws/outpost/<uuid:pk>/", TemplateView.as_view(template_name="if/admin.html")),
    path(
        "ws/client/",
        TemplateView.as_view(template_name="if/admin.html"),
    ),
]
