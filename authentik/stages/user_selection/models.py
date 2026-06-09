"""authentik user selection stage models."""

from typing import TYPE_CHECKING, Any

from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


class UserSelectionStage(Stage):
    """Prompt the user to select a browser-local user."""

    @property
    def serializer(self) -> type[BaseSerializer[Any]]:
        from authentik.stages.user_selection.api import UserSelectionStageSerializer

        return UserSelectionStageSerializer

    @property
    def view(self) -> type[StageView]:
        from authentik.stages.user_selection.stage import UserSelectionStageView

        return UserSelectionStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-selection-form"

    class Meta:
        verbose_name = _("User Selection Stage")
        verbose_name_plural = _("User Selection Stages")
