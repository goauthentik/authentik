"""authentik redirect stage"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Flow, Stage


class RedirectStage(Stage):
    """Redirect the user to another flow, potentially with all gathered context"""

    keep_context = models.BooleanField(default=True)
    target_static = models.CharField(null=True, blank=True)
    target_flow = models.ForeignKey(
        Flow,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_(
            (
                "When set, shows a password field, instead of showing the "
                "password field as separate step."
            ),
        ),
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
