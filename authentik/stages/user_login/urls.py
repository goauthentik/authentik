"""API URLs"""
from authentik.stages.user_login.api import UserLoginStageViewSet

api_urlpatterns = [
    ("stages/user_login", UserLoginStageViewSet),
]
