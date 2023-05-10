"""API URLs"""
from authentik.blueprints.api import BlueprintInstanceViewSet

api_urlpatterns = [
    ("managed/blueprints", BlueprintInstanceViewSet),
]
