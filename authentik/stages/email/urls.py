"""API URLs"""
from authentik.stages.email.api import EmailStageViewSet

api_urlpatterns = [("stages/email", EmailStageViewSet)]
