from enum import StrEnum, auto
from uuid import UUID

import pgtrigger
from django.contrib.contenttypes.fields import ContentType, GenericForeignKey
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.models import TaskBase

from authentik.events.logs import LogEvent
from authentik.events.utils import sanitize_item
from authentik.lib.models import SerializerModel
from authentik.lib.utils.errors import exception_to_string
from authentik.tenants.models import Tenant

CHANNEL_PREFIX = "authentik.tasks"


class ChannelIdentifier(StrEnum):
    ENQUEUE = auto()
    LOCK = auto()


class TaskState(models.TextChoices):
    """Task system-state. Reported by the task runners"""

    QUEUED = "queued"
    CONSUMED = "consumed"
    REJECTED = "rejected"
    DONE = "done"


class Task(SerializerModel, TaskBase):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        help_text=_("Tenant this task belongs to"),
    )

    rel_obj_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    rel_obj_id = models.TextField(null=True)
    rel_obj = GenericForeignKey("rel_obj_content_type", "rel_obj_id")

    _uid = models.TextField(blank=True, null=True)
    _messages = models.JSONField(default=list)

    aggregated_status = models.TextField()

    class Meta(TaskBase.Meta):
        default_permissions = ("view",)
        permissions = [
            ("retrigger_task", _("Restart failed task")),
        ]
        indexes = TaskBase.Meta.indexes + (
            models.Index(fields=("rel_obj_content_type", "rel_obj_id")),
        )
        triggers = TaskBase.Meta.triggers + (
            pgtrigger.Trigger(
                name="update_aggregated_status",
                operation=pgtrigger.Insert | pgtrigger.Update,
                when=pgtrigger.Before,
                func=f"""
                    NEW.aggregated_status := CASE
                        WHEN NEW.state != '{TaskState.DONE.value}' THEN NEW.state
                        ELSE COALESCE((
                            SELECT CASE
                                WHEN bool_or(msg->>'log_level' = 'error') THEN 'error'
                                WHEN bool_or(msg->>'log_level' = 'warning') THEN 'warning'
                                WHEN bool_or(msg->>'log_level' = 'info') THEN 'info'
                                ELSE '{TaskState.DONE.value}'
                            END
                            FROM jsonb_array_elements(NEW._messages) AS msg
                        ), '{TaskState.DONE.value}')
                    END;

                    RETURN NEW;
                """,
            ),
        )

    @property
    def uid(self) -> str:
        uid = str(self.actor_name)
        if self._uid:
            uid += f":{self._uid}"
        return uid

    @property
    def serializer(self):
        from authentik.tasks.api import TaskSerializer

        return TaskSerializer

    def set_uid(self, uid: str | UUID, save: bool = False):
        self._uid = str(uid)
        if save:
            self.save()

    def log(self, log_level: str, message: str | Exception, save: bool = False, **attributes):
        self._messages: list
        if isinstance(message, Exception):
            message = exception_to_string(message)
        log = LogEvent(message, logger=self.uid, log_level=log_level, attributes=attributes)
        self._messages.append(sanitize_item(log))
        if save:
            self.save()

    def info(self, message: str | Exception, save: bool = False, **attributes):
        self.log("info", message, save=save, **attributes)

    def warning(self, message: str | Exception, save: bool = False, **attributes):
        self.log("warning", message, save=save, **attributes)

    def error(self, message: str | Exception, save: bool = False, **attributes):
        self.log("error", message, save=save, **attributes)
