"""API URLs"""
from authentik.stages.identification.api import IdentificationStageViewSet

api_urlpatterns = [("stages/identification", IdentificationStageViewSet)]
