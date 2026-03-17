import pickle  # nosec
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dramatiq.actor import Actor
from psqlextra.types import ConflictAction

if TYPE_CHECKING:
    from authentik.tasks.schedules.models import Schedule


@dataclass
class ScheduleSpec:
    actor: Actor
    crontab: str
    paused: bool = False
    identifier: str | UUID | None = None
    uid: str | None = None

    args: Iterable[Any] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)

    rel_obj: Any | None = None

    send_on_save: bool = False

    send_on_startup: bool = False

    def get_args(self) -> bytes:
        return pickle.dumps(self.args)

    def get_kwargs(self) -> bytes:
        return pickle.dumps(self.kwargs)

    def get_options(self) -> bytes:
        options = self.options
        if self.uid is not None:
            options["uid"] = self.uid
        return pickle.dumps(options)

    def update_or_create(self) -> Schedule:
        from django.contrib.contenttypes.models import ContentType

        from authentik.tasks.schedules.models import Schedule

        update_values = {
            "_uid": self.uid,
            "paused": self.paused,
            "args": self.get_args(),
            "kwargs": self.get_kwargs(),
            "options": self.get_options(),
        }
        if self.rel_obj is not None:
            update_values["rel_obj_content_type"] = ContentType.objects.get_for_model(self.rel_obj)
            update_values["rel_obj_id"] = str(self.rel_obj.pk)
        create_values = {
            **update_values,
            "crontab": self.crontab,
        }

        schedule = Schedule.objects.on_conflict(
            ["actor_name", "identifier"],
            ConflictAction.UPDATE,
            update_values=update_values,
        ).insert_and_get(
            actor_name=self.actor.actor_name,
            identifier=str(self.identifier),
            **create_values,
        )

        return schedule
