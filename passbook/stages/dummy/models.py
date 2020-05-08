"""dummy stage models"""
from django.utils.translation import gettext as _

from passbook.flows.models import Stage


class DummyStage(Stage):
    """Dummy stage, mostly used to debug"""

    type = "passbook.stages.dummy.stage.DummyStage"
    form = "passbook.stages.dummy.forms.DummyStageForm"

    def __str__(self):
        return f"Dummy Stage {self.name}"

    class Meta:

        verbose_name = _("Dummy Stage")
        verbose_name_plural = _("Dummy Stages")
