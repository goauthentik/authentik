"""OAuth provider URLs"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from authentik.providers.oauth2.constants import SCOPE_OPENID
from authentik.providers.oauth2.utils import protected_resource_view
from authentik.providers.oauth2.views.authorize import AuthorizationFlowInitView
from authentik.providers.oauth2.views.introspection import TokenIntrospectionView
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.providers.oauth2.views.session import EndSessionView
from authentik.providers.oauth2.views.token import TokenView
from authentik.providers.oauth2.views.userinfo import UserInfoView

urlpatterns = [
    path(
        "authorize/",
        AuthorizationFlowInitView.as_view(),
        name="authorize",
    ),
    path("token/", csrf_exempt(TokenView.as_view()), name="token"),
    path(
        "userinfo/",
        csrf_exempt(protected_resource_view([SCOPE_OPENID])(UserInfoView.as_view())),
        name="userinfo",
    ),
    path(
        "introspect/",
        csrf_exempt(TokenIntrospectionView.as_view()),
        name="token-introspection",
    ),
    path(
        "<slug:application_slug>/end-session/",
        EndSessionView.as_view(),
        name="end-session",
    ),
    path("<slug:application_slug>/jwks/", JWKSView.as_view(), name="jwks"),
    path(
        "<slug:application_slug>/.well-known/openid-configuration",
        ProviderInfoView.as_view(),
        name="provider-info",
    ),
]
