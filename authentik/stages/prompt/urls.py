"""API URLs"""

from authentik.stages.prompt.api.prompts import PromptViewSet
from authentik.stages.prompt.api.stages import PromptStageViewSet

api_urlpatterns = [
    ("stages/prompt/prompts", PromptViewSet),
    ("stages/prompt/stages", PromptStageViewSet),
]
