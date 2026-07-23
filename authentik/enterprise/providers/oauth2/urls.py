"""OAuth2 Dynamic Client Registration URLs"""

from django.urls import path

from authentik.enterprise.providers.oauth2.api import OAuth2DynamicClientRegistrationViewSet
from authentik.enterprise.providers.oauth2.views.dcr import DynamicClientRegistrationView

urlpatterns = [
    path(
        "<slug:application_slug>/register/",
        DynamicClientRegistrationView.as_view(),
        name="dynamic-client-registration",
    ),
]

api_urlpatterns = [
    ("providers/oauth2/dcr", OAuth2DynamicClientRegistrationViewSet),
]
