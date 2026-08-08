from django.urls import path

from authentik.sources.bsky.api.property_mappings import BskySourcePropertyMappingViewSet
from authentik.sources.bsky.api.source import BskySourceViewSet
from authentik.sources.bsky.api.source_connection import (
    GroupBskySourceConnectionViewSet,
    UserBskySourceConnectionViewSet,
)
from authentik.sources.bsky.views.callback import BskyCallbackView
from authentik.sources.bsky.views.metadata import ClientJWKSView, ClientMetadataView
from authentik.sources.bsky.views.redirect import BskyLoginView

urlpatterns = [
    path(
        "<slug:source_slug>/client-metadata.json",
        ClientMetadataView.as_view(),
        name="oauth-client-metadata",
    ),
    path(
        "<slug:source_slug>/jwks.json",
        ClientJWKSView.as_view(),
        name="oauth-client-jwks",
    ),
    path(
        "<slug:source_slug>/login/",
        BskyLoginView.as_view(),
        name="oauth-client-login",
    ),
    path(
        "<slug:source_slug>/callback/",
        BskyCallbackView.as_view(),
        name="oauth-client-callback",
    ),
]

api_urlpatterns = [
    ("propertymappings/source/bsky", BskySourcePropertyMappingViewSet),
    ("sources/user_connections/bsky", UserBskySourceConnectionViewSet),
    ("sources/group_connections/bsky", GroupBskySourceConnectionViewSet),
    ("sources/bsky", BskySourceViewSet),
]
