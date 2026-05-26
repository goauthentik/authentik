"""API URLs."""

from authentik.stages.account_selection.api import (
    AccountSelectionStageViewSet,
    AccountSwitchStageViewSet,
)

api_urlpatterns = [
    ("stages/account_selection/selection", AccountSelectionStageViewSet),
    ("stages/account_selection/switch", AccountSwitchStageViewSet),
]
