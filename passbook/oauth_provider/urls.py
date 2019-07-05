"""passbook oauth_provider urls"""

from django.urls import path
from oauth2_provider import views

from passbook.oauth_provider.views import oauth2

urlpatterns = [
    # Custom OAuth 2 Authorize View
    path('authorize/', oauth2.PassbookAuthorizationLoadingView.as_view(),
         name="oauth2-authorize"),
    path('authorize/permission_ok/', oauth2.PassbookAuthorizationView.as_view(),
         name="oauth2-ok-authorize"),
    path('authorize/permission_denied/', oauth2.OAuthPermissionDenied.as_view(),
         name='oauth2-permission-denied'),
    # OAuth API
    path("token/", views.TokenView.as_view(), name="token"),
    path("revoke_token/", views.RevokeTokenView.as_view(), name="revoke-token"),
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
]
