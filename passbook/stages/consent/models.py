"""passbook consent stage"""
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class ConsentStage(Stage):
    """Prompt the user for confirmation."""

    type = "passbook.stages.consent.stage.ConsentStage"
    form = "passbook.stages.consent.forms.ConsentStageForm"

    def __str__(self):
        return f"Consent Stage {self.name}"

    class Meta:

        verbose_name = _("Consent Stage")
        verbose_name_plural = _("Consent Stages")
