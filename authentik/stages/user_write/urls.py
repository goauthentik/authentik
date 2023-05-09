"""API URLs"""
from authentik.stages.user_write.api import UserWriteStageViewSet

api_urlpatterns = [("stages/user_write", UserWriteStageViewSet)]
