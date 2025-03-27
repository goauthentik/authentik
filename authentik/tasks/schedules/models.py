from uuid import uuid4
from cron_converter import Cron

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import datetime

from authentik.lib.models import SerializerModel


def validate_crontab(value):
    try:
        Cron(value)
    except ValueError as exc:
        raise ValidationError(
            _("%(value)s is not a valid crontab"),
            params={"value": value},
        ) from exc


class Schedule(SerializerModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    uid = models.TextField(unique=True, editable=False)

    name = models.TextField(editable=False, help_text=_("Schedule display name"))

    actor_name = models.TextField(editable=False, help_text=_("Dramatiq actor to call"))
    args = models.BinaryField(editable=False, help_text=_("Args to send to the actor"))
    kwargs = models.BinaryField(editable=False, help_text=_("Kwargs to send to the actor"))

    crontab = models.TextField(validators=[validate_crontab])

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

    def calculate_next_run(self, next_run: datetime) -> datetime:
        return Cron(self.crontab).schedule(next_run).next()
