"""passbook oauth_provider urls"""

from django.urls import include, path

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
    path('', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
