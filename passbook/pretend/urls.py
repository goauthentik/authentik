"""passbook pretend urls"""
from django.urls import include, path
from oauth2_provider.views import TokenView

from passbook.oauth_provider.views.oauth2 import PassbookAuthorizationView
from passbook.pretend.views.github import GitHubUserView

github_urlpatterns = [
    path('login/oauth/authorize', PassbookAuthorizationView.as_view(), name='github-authorize'),
    path('login/oauth/access_token', TokenView.as_view(), name='github-access-token'),
    path('user', GitHubUserView.as_view(), name='github-user'),
]

urlpatterns = [
    path('', include(github_urlpatterns))
]
