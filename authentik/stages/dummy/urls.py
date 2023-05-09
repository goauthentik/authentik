"""API URLs"""
from authentik.stages.dummy.api import DummyStageViewSet

api_urlpatterns = [("stages/dummy", DummyStageViewSet)]
