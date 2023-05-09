"""API URLs"""
from authentik.stages.prompt.api import PromptStageViewSet, PromptViewSet

api_urlpatterns = [
    ("stages/prompt/prompts", PromptViewSet),
    ("stages/prompt/stages", PromptStageViewSet),
]
