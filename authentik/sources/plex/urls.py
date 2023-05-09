"""API URLs"""
from authentik.sources.plex.api.source import PlexSourceViewSet
from authentik.sources.plex.api.source_connection import PlexSourceConnectionViewSet

api_urlpatterns = [
    ("sources/user_connections/plex", PlexSourceConnectionViewSet),
    ("sources/plex", PlexSourceViewSet),
]
