"""API URLs."""

from authentik.stages.user_selection.api import (
    UserSelectionStageViewSet,
)

api_urlpatterns = [
    ("stages/user_selection/selection", UserSelectionStageViewSet),
]
