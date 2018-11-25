"""passbook oauth_provider urls"""

from django.urls import include, path

from passbook.oauth_provider.views import oauth2

urlpatterns = [
    # Custom OAuth 2 Authorize View
    path('authorize/', oauth2.PassbookAuthorizationView.as_view(), name="oauth2-authorize"),
    # OAuth API
    path('', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
