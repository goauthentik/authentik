import pickle  # nosec
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dramatiq.actor import Actor

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
        return pickle.dumps(self.options)

    def update_or_create(self) -> "Schedule":
        from authentik.tasks.schedules.models import Schedule

        query = {
            "actor_name": self.actor.actor_name,
            "identifier": self.identifier,
        }
        defaults = {
            **query,
            "_uid": self.uid,
            "paused": self.paused,
            "args": self.get_args(),
            "kwargs": self.get_kwargs(),
            "options": self.get_options(),
        }
        create_defaults = {
            **defaults,
            "crontab": self.crontab,
            "rel_obj": self.rel_obj,
        }

        schedule, _ = Schedule.objects.update_or_create(
            **query,
            defaults=defaults,
            create_defaults=create_defaults,
        )

        return schedule
