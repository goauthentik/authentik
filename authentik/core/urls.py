"""authentik URL Configuration"""
from channels.auth import AuthMiddleware
from channels.sessions import CookieMiddleware
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView

from authentik.core.api.applications import ApplicationViewSet
from authentik.core.api.authenticated_sessions import AuthenticatedSessionViewSet
from authentik.core.api.devices import AdminDeviceViewSet, DeviceViewSet
from authentik.core.api.groups import GroupViewSet
from authentik.core.api.propertymappings import PropertyMappingViewSet
from authentik.core.api.providers import ProviderViewSet
from authentik.core.api.sources import SourceViewSet, UserSourceConnectionViewSet
from authentik.core.api.tokens import TokenViewSet
from authentik.core.api.transactional_applications import TransactionalApplicationView
from authentik.core.api.users import UserViewSet
from authentik.core.views import apps
from authentik.core.views.debug import AccessDeniedView
from authentik.core.views.interface import FlowInterfaceView, InterfaceView
from authentik.core.views.session import EndSessionView
from authentik.root.asgi_middleware import SessionMiddleware
from authentik.root.messages.consumer import MessageConsumer
from authentik.root.middleware import ChannelsLoggingMiddleware

urlpatterns = [
    path(
        "",
        login_required(
            RedirectView.as_view(pattern_name="authentik_core:if-user", query_string=True)
        ),
        name="root-redirect",
    ),
    path(
        # We have to use this format since everything else uses applications/o or applications/saml
        "application/launch/<slug:application_slug>/",
        apps.RedirectToAppLaunch.as_view(),
        name="application-launch",
    ),
    # Interfaces
    path(
        "if/admin/",
        ensure_csrf_cookie(InterfaceView.as_view(template_name="if/admin.html")),
        name="if-admin",
    ),
    path(
        "if/user/",
        ensure_csrf_cookie(InterfaceView.as_view(template_name="if/user.html")),
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
    path("ws/outpost/<uuid:pk>/", InterfaceView.as_view(template_name="if/admin.html")),
    path(
        "ws/client/",
        InterfaceView.as_view(template_name="if/admin.html"),
    ),
]

api_urlpatterns = [
    ("core/authenticated_sessions", AuthenticatedSessionViewSet),
    ("core/applications", ApplicationViewSet),
    path(
        "core/transactional/applications/",
        TransactionalApplicationView.as_view(),
        name="core-transactional-application",
    ),
    ("core/groups", GroupViewSet),
    ("core/users", UserViewSet),
    ("core/tokens", TokenViewSet),
    ("sources/all", SourceViewSet),
    ("sources/user_connections/all", UserSourceConnectionViewSet),
    ("providers/all", ProviderViewSet),
    ("propertymappings/all", PropertyMappingViewSet),
    ("authenticators/all", DeviceViewSet, "device"),
    (
        "authenticators/admin/all",
        AdminDeviceViewSet,
        "admin-device",
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
