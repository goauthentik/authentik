"""API URLs"""

from authentik.stages.redirect.api import RedirectStageViewSet

api_urlpatterns = [("stages/redirect", RedirectStageViewSet)]
