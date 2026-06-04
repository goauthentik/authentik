"""authentik account selection stage models."""

from typing import TYPE_CHECKING, Any

from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


class AccountSelectionStage(Stage):
    """Prompt the user to select a browser-local account."""

    @property
    def serializer(self) -> type[BaseSerializer[Any]]:
        from authentik.stages.account_selection.api import AccountSelectionStageSerializer

        return AccountSelectionStageSerializer

    @property
    def view(self) -> type[StageView]:
        from authentik.stages.account_selection.stage import AccountSelectionStageView

        return AccountSelectionStageView

    @property
    def component(self) -> str:
        return "ak-stage-account-selection-form"

    class Meta:
        verbose_name = _("Account Selection Stage")
        verbose_name_plural = _("Account Selection Stages")


class AccountSwitchStage(Stage):
    """Activate the account selected by an earlier Account Selection stage."""

    @property
    def serializer(self) -> type[BaseSerializer[Any]]:
        from authentik.stages.account_selection.api import AccountSwitchStageSerializer

        return AccountSwitchStageSerializer

    @property
    def view(self) -> type[StageView]:
        from authentik.stages.account_selection.stage import AccountSwitchStageView

        return AccountSwitchStageView

    @property
    def component(self) -> str:
        return "ak-stage-account-switch-form"

    class Meta:
        verbose_name = _("Account Switch Stage")
        verbose_name_plural = _("Account Switch Stages")
