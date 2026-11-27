"""authentik oauth_provider urls"""

from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path

from authentik.providers.oauth2.views.authorize import AuthorizationFlowInitView
from authentik.providers.oauth2.views.device_init import DeviceEntryView
from authentik.providers.oauth2.views.github import GitHubUserTeamsView, GitHubUserView
from authentik.providers.oauth2.views.provider import ProviderInfoView
from authentik.providers.oauth2.views.token import TokenView

github_urlpatterns = [
    path(
        "login/oauth/authorize",
        AuthorizationFlowInitView.as_view(github_compat=True),
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
    path(
        "device",
        login_required(
            DeviceEntryView.as_view(),
        ),
        name="device-login",
    ),
    # RFC 8414 section 3.1 removes the issuer's terminating "/" before inserting the well-known
    # path, so the metadata of the issuer ".../application/o/<slug>/" is served without a
    # trailing slash. The trailing-slash form, the only one served before, keeps working.
    re_path(
        r"^\.well-known/oauth-authorization-server/application/o/(?P<application_slug>[-a-zA-Z0-9_]+)/?$",
        ProviderInfoView.as_view(),
        name="providers-oauth2-authorization-server-metadata",
    ),
]
