"""passbook oauth_client urls"""

from django.urls import path

from passbook.oauth_client.source_types.manager import RequestKind
# from passbook.oauth_client.views import core, settings
from passbook.oauth_client.views import dispatcher

# from passbook.oauth_client.views.providers import (discord, facebook, github,
#                                                    google, reddit, supervisr,
#                                                    twitter)

urlpatterns = [
    # # Supervisr
    # url(r'^callback/(?P<provider>supervisr)/$',
    #     supervisr.SupervisrOAuthCallback.as_view(), name='oauth-client-callback'),
    # # Twitter
    # url(r'^callback/(?P<provider>twitter)/$',
    #     twitter.TwitterOAuthCallback.as_view(), name='oauth-client-callback'),
    # # GitHub
    # url(r'^callback/(?P<provider>github)/$',
    #     github.GitHubOAuth2Callback.as_view(), name='oauth-client-callback'),
    # # Facebook
    # url(r'^callback/(?P<provider>facebook)/$',
    #     facebook.FacebookOAuth2Callback.as_view(), name='oauth-client-callback'),
    # url(r'^login/(?P<provider>facebook)/$',
    #     facebook.FacebookOAuthRedirect.as_view(), name='oauth-client-login'),
    # # Discord
    # url(r'^callback/(?P<provider>discord)/$',
    #     discord.DiscordOAuth2Callback.as_view(), name='oauth-client-callback'),
    # url(r'^login/(?P<provider>discord)/$',
    #     discord.DiscordOAuthRedirect.as_view(), name='oauth-client-login'),
    # # Reddit
    # url(r'^callback/(?P<provider>reddit)/$',
    #     reddit.RedditOAuth2Callback.as_view(), name='oauth-client-callback'),
    # url(r'^login/(?P<provider>reddit)/$',
    #     reddit.RedditOAuthRedirect.as_view(), name='oauth-client-login'),
    # # Google
    # url(r'^callback/(?P<provider>google)/$',
    #     google.GoogleOAuth2Callback.as_view(), name='oauth-client-callback'),
    # url(r'^login/(?P<provider>google)/$',
    #     google.GoogleOAuthRedirect.as_view(), name='oauth-client-login'),
    path('login/<slug:source_slug>/', dispatcher.DispatcherView.as_view(
        kind=RequestKind.redirect), name='oauth-client-login'),
    path('callback/<slug:source_slug>/', dispatcher.DispatcherView.as_view(
        kind=RequestKind.callback), name='oauth-client-callback'),
    # path('disconnect/<slug:source_slug>/', core.disconnect,
    #     name='oauth-client-disconnect'),
]
