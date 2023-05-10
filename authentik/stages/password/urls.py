"""API URLs"""
from authentik.stages.password.api import PasswordStageViewSet

api_urlpatterns = [("stages/password", PasswordStageViewSet)]
