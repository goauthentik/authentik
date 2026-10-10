"""API URLs"""

from authentik.stages.message.api import MessageStageViewSet

api_urlpatterns = [("stages/message", MessageStageViewSet, "stages-message")]
