"""OAuth provider URLs"""
from django.urls import path
from django.views.generic.base import RedirectView

from authentik.providers.oauth2.api.providers import OAuth2ProviderViewSet
from authentik.providers.oauth2.api.scopes import ScopeMappingViewSet
from authentik.providers.oauth2.api.tokens import (
    AccessTokenViewSet,
    AuthorizationCodeViewSet,
    RefreshTokenViewSet,
)
from authentik.providers.oauth2.views.authorize import AuthorizationFlowInitView
from authentik.providers.oauth2.views.device_backchannel import DeviceView
from authentik.providers.oauth2.views.introspection import TokenIntrospectionView
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.providers.oauth2.views.token import TokenView
from authentik.providers.oauth2.views.token_revoke import TokenRevokeView
from authentik.providers.oauth2.views.userinfo import UserInfoView

urlpatterns = [
    path(
        "authorize/",
        AuthorizationFlowInitView.as_view(),
        name="authorize",
    ),
    path("token/", TokenView.as_view(), name="token"),
    path("device/", DeviceView.as_view(), name="device"),
    path(
        "userinfo/",
        UserInfoView.as_view(),
        name="userinfo",
    ),
    path(
        "introspect/",
        TokenIntrospectionView.as_view(),
        name="token-introspection",
    ),
    path(
        "revoke/",
        TokenRevokeView.as_view(),
        name="token-revoke",
    ),
    path(
        "<slug:application_slug>/end-session/",
        RedirectView.as_view(pattern_name="authentik_core:if-session-end", query_string=True),
        name="end-session",
    ),
    path("<slug:application_slug>/jwks/", JWKSView.as_view(), name="jwks"),
    path(
        "<slug:application_slug>/",
        RedirectView.as_view(pattern_name="authentik_providers_oauth2:provider-info"),
        name="provider-root",
    ),
    path(
        "<slug:application_slug>/.well-known/openid-configuration",
        ProviderInfoView.as_view(),
        name="provider-info",
    ),
]

api_urlpatterns = [
    ("providers/oauth2", OAuth2ProviderViewSet),
    ("propertymappings/scope", ScopeMappingViewSet),
    ("oauth2/authorization_codes", AuthorizationCodeViewSet),
    ("oauth2/refresh_tokens", RefreshTokenViewSet),
    ("oauth2/access_tokens", AccessTokenViewSet),
]
