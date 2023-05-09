"""API URLs"""
from authentik.stages.user_delete.api import UserDeleteStageViewSet

api_urlpatterns = [("stages/user_delete", UserDeleteStageViewSet)]
