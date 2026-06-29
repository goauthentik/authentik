from django.urls import path

from authentik.enterprise.providers.scim.views import SCIMOAuthStart, SCIMRedirectCallback

urlpatterns = [
    path("<slug:application_slug>/oauth2/start/", SCIMOAuthStart.as_view(), name="start"),
    path(
        "<slug:application_slug>/oauth2/callback/", SCIMRedirectCallback.as_view(), name="callback"
    ),
]
