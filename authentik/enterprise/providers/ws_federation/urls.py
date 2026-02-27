"""WS Fed provider URLs"""

from django.urls import path

from authentik.enterprise.providers.ws_federation.api.providers import WSFederationProviderViewSet
from authentik.enterprise.providers.ws_federation.views import WSFedEntryView
from authentik.providers.saml.views.metadata import MetadataDownload

urlpatterns = [
    path(
        "",
        WSFedEntryView.as_view(),
        name="wsfed",
    ),
    # Metadata
    path(
        "<slug:application_slug>/metadata/",
        MetadataDownload.as_view(),
        name="metadata-download",
    ),
]

api_urlpatterns = [
    ("providers/wsfed", WSFederationProviderViewSet),
]
