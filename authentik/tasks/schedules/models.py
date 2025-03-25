from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.lib.models import SerializerModel


class Schedule(SerializerModel):
    id = models.TextField(primary_key=True, editable=False)

    name = models.TextField(editable=False, help_text=_("Schedule display name"))

    actor_name = models.TextField(editable=False, help_text=_("Dramatiq actor to call"))
    args = models.BinaryField(editable=False, help_text=_("Args to send to the actor"))
    kwargs = models.BinaryField(editable=False, help_text=_("Kwargs to send to the actor"))

    crontab = models.TextField()

    next_run = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")
        default_permissions = (
            "change",
            "view",
        )

    def __str__(self):
        return self.name

    @property
    def serializer(self):
        from authentik.tasks.schedules.api import ScheduleSerializer

        return ScheduleSerializer
