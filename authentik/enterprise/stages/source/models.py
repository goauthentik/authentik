"""Source stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage
from authentik.lib.utils.time import timedelta_string_validator


class SourceStage(Stage):
    """Suspend the current flow execution and send the user to a source,
    after which this flow execution is resumed."""

    source = models.ForeignKey("authentik_core.Source", on_delete=models.CASCADE)

    resume_timeout = models.TextField(
        default="minutes=10",
        validators=[timedelta_string_validator],
        help_text=_(
            "Amount of time a user can take to return from the source to continue the flow "
            "(Format: hours=-1;minutes=-2;seconds=-3)"
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.stages.source.api import SourceStageSerializer

        return SourceStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.enterprise.stages.source.stage import SourceStageView

        return SourceStageView

    @property
    def component(self) -> str:
        return "ak-stage-source-form"

    class Meta:
        verbose_name = _("Source Stage")
        verbose_name_plural = _("Source Stages")
