"""authentik oauth_provider urls"""
from django.urls import include, path

from authentik.providers.oauth2.views.authorize import AuthorizationFlowInitView
from authentik.providers.oauth2.views.github import GitHubUserTeamsView, GitHubUserView
from authentik.providers.oauth2.views.token import TokenView

github_urlpatterns = [
    path(
        "login/oauth/authorize",
        AuthorizationFlowInitView.as_view(),
        name="github-authorize",
    ),
    path(
        "login/oauth/access_token",
        TokenView.as_view(),
        name="github-access-token",
    ),
    path(
        "user",
        GitHubUserView.as_view(),
        name="github-user",
    ),
    path(
        "user/teams",
        GitHubUserTeamsView.as_view(),
        name="github-user-teams",
    ),
]

urlpatterns = [
    path("", include(github_urlpatterns)),
]
