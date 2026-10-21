"""message stage models"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from authentik.flows.stage import StageView

from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class MessageStage(Stage):
    """Display a message to the user."""

    title = models.TextField(blank=True, default="")
    message = models.TextField()
    button_text = models.TextField(blank=True, default="")

    @property
    def serializer(self) -> type[BaseSerializer[Any]]:
        from authentik.stages.message.api import MessageStageSerializer

        return MessageStageSerializer

    @property
    def view(self) -> type[StageView]:
        from authentik.stages.message.stage import MessageStageView
        return MessageStageView

    @property
    def component(self) -> str:
        return "ak-stage-message-form"

    class Meta:
        verbose_name = _("Message Stage")
        verbose_name_plural = _("Message Stages")
