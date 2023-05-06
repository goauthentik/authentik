"""authentik URL Configuration"""
from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from authentik.core.views import apps, impersonate
from authentik.core.views.debug import AccessDeniedView
from authentik.core.views.session import EndSessionView
from authentik.interfaces.models import InterfaceType
from authentik.interfaces.views import RedirectToInterface
from authentik.root.asgi_middleware import SessionMiddleware
from authentik.root.messages.consumer import MessageConsumer
from authentik.root.middleware import ChannelsLoggingMiddleware


def placeholder_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    """Empty view used as placeholder

    (Mounted to websocket endpoints and used by e2e tests)"""
    return HttpResponse(status_code=200)


urlpatterns = [
    path(
        "",
        login_required(RedirectToInterface.as_view(type=InterfaceType.USER)),
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
        "if/session-end/<slug:application_slug>/",
        ensure_csrf_cookie(EndSessionView.as_view()),
        name="if-session-end",
    ),
    # Fallback for WS
    path("ws/outpost/<uuid:pk>/", placeholder_view),
    path(
        "ws/client/",
        placeholder_view,
    ),
]

websocket_urlpatterns = [
    path(
        "ws/client/",
        ChannelsLoggingMiddleware(
            CookieMiddleware(SessionMiddleware(AuthMiddleware(MessageConsumer.as_asgi())))
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("debug/policy/deny/", AccessDeniedView.as_view(), name="debug-policy-deny"),
    ]
