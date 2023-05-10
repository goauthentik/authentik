"""API URLs"""
from authentik.stages.deny.api import DenyStageViewSet

api_urlpatterns = [("stages/deny", DenyStageViewSet)]
