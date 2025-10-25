"""API URLs"""

from authentik.sources.plex.api.property_mappings import PlexSourcePropertyMappingViewSet
from authentik.sources.plex.api.source import PlexSourceViewSet
from authentik.sources.plex.api.source_connection import (
    GroupPlexSourceConnectionViewSet,
    UserPlexSourceConnectionViewSet,
)

api_urlpatterns = [
    ("propertymappings/source/plex", PlexSourcePropertyMappingViewSet),
    ("sources/user_connections/plex", UserPlexSourceConnectionViewSet),
    ("sources/group_connections/plex", GroupPlexSourceConnectionViewSet),
    ("sources/plex", PlexSourceViewSet),
]
