import pickle  # nosec
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dramatiq.actor import Actor
from psqlextra.query import ConflictAction

if TYPE_CHECKING:
    from authentik.tasks.schedules.models import Schedule


@dataclass
class ScheduleSpec:
    actor: Actor
    crontab: str
    paused: bool = False
    identifier: str | None = None
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

    def update_or_create(self) -> "Schedule":
        from authentik.tasks.schedules.models import Schedule

        update_values = {
            "_uid": self.uid,
            "paused": self.paused,
            "args": self.get_args(),
            "kwargs": self.get_kwargs(),
            "options": self.get_options(),
        }
        create_values = {
            **update_values,
            "crontab": self.crontab,
            "rel_obj": self.rel_obj,
        }

        schedule = Schedule.objects.on_conflict(
            ["actor_name", "identifier"],
            ConflictAction.UPDATE,
            update_values=update_values,
        ).insert_and_get(
            actor_name=self.actor.actor_name,
            identifier=self.identifier,
            **create_values,
        )

        return schedule
