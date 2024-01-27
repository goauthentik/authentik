"""API URLs"""
from authentik.stages.source.api import SourceStageViewSet

api_urlpatterns = [("stages/source", SourceStageViewSet)]
