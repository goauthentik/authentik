from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.models import ScheduleBase

from authentik.lib.models import SerializerModel
from authentik.tasks.models import TasksModel
from authentik.tasks.schedules.common import ScheduleSpec


class Schedule(TasksModel, SerializerModel, ScheduleBase):
    identifier = models.TextField(
        editable=False,
        null=True,
        help_text=_("Unique schedule identifier"),
    )
    _uid = models.TextField(
        blank=True,
        null=True,
        help_text=_("User schedule identifier"),
    )

    rel_obj_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    rel_obj_id = models.TextField(null=True)
    rel_obj = GenericForeignKey("rel_obj_content_type", "rel_obj_id")

    class Meta(ScheduleBase.Meta):
        default_permissions = (
            "change",
            "view",
        )
        permissions = [
            ("send_schedule", _("Manually trigger a schedule")),
        ]
        indexes = (models.Index(fields=("rel_obj_content_type", "rel_obj_id")),)
        unique_together = (
            (
                "actor_name",
                "identifier",
            ),
        )

    def __str__(self):
        return f"Schedule {self.actor_name}:{self.uid}"

    @property
    def uid(self) -> str:
        uid = str(self.actor_name)
        if self._uid:
            uid += f":{self._uid}"
        return uid

    @property
    def serializer(self):
        from authentik.tasks.schedules.api import ScheduleSerializer

        return ScheduleSerializer


class ScheduledModel(TasksModel, models.Model):
    schedules = GenericRelation(
        Schedule, content_type_field="rel_obj_content_type", object_id_field="rel_obj_id"
    )

    class Meta:
        abstract = True

    @classmethod
    def models(cls) -> list[models.Model]:
        def is_scheduled_model(klass) -> bool:
            if ScheduledModel in klass.__bases__:
                return True
            return any(is_scheduled_model(klass) for klass in klass.__bases__)

        return [
            model
            for model in apps.get_models()
            if is_scheduled_model(model) and not model.__subclasses__()
        ]

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        raise NotImplementedError
