"""authentik oauth_provider urls"""
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from authentik.providers.oauth2.constants import SCOPE_GITHUB_ORG_READ, SCOPE_GITHUB_USER_EMAIL
from authentik.providers.oauth2.utils import protected_resource_view
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
        csrf_exempt(TokenView.as_view()),
        name="github-access-token",
    ),
    path(
        "user",
        csrf_exempt(protected_resource_view([SCOPE_GITHUB_USER_EMAIL])(GitHubUserView.as_view())),
        name="github-user",
    ),
    path(
        "user/teams",
        csrf_exempt(
            protected_resource_view([SCOPE_GITHUB_ORG_READ])(GitHubUserTeamsView.as_view())
        ),
        name="github-user-teams",
    ),
]

urlpatterns = [
    path("", include(github_urlpatterns)),
]
