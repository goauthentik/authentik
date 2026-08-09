"""API URLs"""

from authentik.enterprise.stages.source.api import SourceStageViewSet

api_urlpatterns = [("stages/source", SourceStageViewSet)]
