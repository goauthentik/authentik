"""authentik redirect stage"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Flow, Stage


class RedirectMode(models.TextChoices):
    """Mode a Redirect stage can operate in"""

    STATIC = "static"
    FLOW = "flow"


class RedirectStage(Stage):
    """Redirect the user to another flow, potentially with all gathered context"""

    keep_context = models.BooleanField(default=True)
    mode = models.TextField(choices=RedirectMode.choices)
    target_static = models.CharField(blank=True, default="")
    target_flow = models.ForeignKey(
        Flow,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.redirect.api import RedirectStageSerializer

        return RedirectStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.redirect.stage import RedirectStageView

        return RedirectStageView

    @property
    def component(self) -> str:
        return "ak-stage-redirect-form"

    class Meta:
        verbose_name = _("Redirect Stage")
        verbose_name_plural = _("Redirect Stages")
