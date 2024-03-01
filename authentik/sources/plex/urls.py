"""API URLs"""

from authentik.sources.plex.api.property_mapping import PlexSourcePropertyMappingViewSet
from authentik.sources.plex.api.source import PlexSourceViewSet
from authentik.sources.plex.api.source_connection import PlexSourceConnectionViewSet

api_urlpatterns = [
    ("propertymappings/plex_source", PlexSourcePropertyMappingViewSet),
    ("sources/user_connections/plex", PlexSourceConnectionViewSet),
    ("sources/plex", PlexSourceViewSet),
]
