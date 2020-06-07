"""passbook oauth_provider urls"""

from django.urls import include, path
from oauth2_provider import views

from passbook.providers.oauth.views import github, oauth2

oauth_urlpatterns = [
    # Custom OAuth2 Authorize View
    path(
        "authorize/",
        oauth2.AuthorizationFlowInitView.as_view(),
        name="oauth2-authorize",
    ),
    # OAuth API
    path("token/", views.TokenView.as_view(), name="token"),
    path("revoke_token/", views.RevokeTokenView.as_view(), name="revoke-token"),
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
]

github_urlpatterns = [
    path(
        "login/oauth/authorize",
        oauth2.AuthorizationFlowInitView.as_view(),
        name="github-authorize",
    ),
    path(
        "login/oauth/access_token",
        views.TokenView.as_view(),
        name="github-access-token",
    ),
    path("user", github.GitHubUserView.as_view(), name="github-user"),
    path("user/teams", github.GitHubUserTeamsView.as_view(), name="github-user-teams"),
]

urlpatterns = [
    path("", include(github_urlpatterns)),
    path("application/oauth/", include(oauth_urlpatterns)),
]
