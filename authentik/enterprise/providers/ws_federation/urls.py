"""WS Fed provider URLs"""

from django.urls import path

from authentik.enterprise.providers.ws_federation.api.providers import WSFederationProviderViewSet
from authentik.enterprise.providers.ws_federation.views import WSFedEntryView

urlpatterns = [
    path(
        "",
        WSFedEntryView.as_view(),
        name="wsfed",
    ),
]

api_urlpatterns = [
    ("providers/wsfed", WSFederationProviderViewSet),
]
