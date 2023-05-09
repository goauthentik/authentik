"""API URLs"""
from authentik.stages.user_logout.api import UserLogoutStageViewSet

api_urlpatterns = [("stages/user_logout", UserLogoutStageViewSet)]
