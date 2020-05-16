"""passbook oauth_provider urls"""

from django.urls import include, path
from oauth2_provider import views

from passbook.providers.oauth.views import github, oauth2

oauth_urlpatterns = [
    # Custom OAuth 2 Authorize View
    path(
        "authorize/",
        oauth2.PassbookAuthorizationLoadingView.as_view(),
        name="oauth2-authorize",
    ),
    path(
        "authorize/permission_ok/",
        oauth2.PassbookAuthorizationView.as_view(),
        name="oauth2-ok-authorize",
    ),
    path(
        "authorize/permission_denied/",
        oauth2.OAuthPermissionDenied.as_view(),
        name="oauth2-permission-denied",
    ),
    # OAuth API
    path("token/", views.TokenView.as_view(), name="token"),
    path("revoke_token/", views.RevokeTokenView.as_view(), name="revoke-token"),
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
]

github_urlpatterns = [
    path(
        "login/oauth/authorize",
        oauth2.PassbookAuthorizationView.as_view(),
        name="github-authorize",
    ),
    path(
        "login/oauth/access_token",
        views.TokenView.as_view(),
        name="github-access-token",
    ),
    path("user", github.GitHubUserView.as_view(), name="github-user"),
]

urlpatterns = [
    path("", include(github_urlpatterns)),
    path("application/oauth/", include(oauth_urlpatterns)),
]
