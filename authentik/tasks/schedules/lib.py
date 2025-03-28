import pickle  # nosec
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScheduleSpec:
    actor_name: str
    crontab: str
    uid: str | None = None

    args: Iterable[Any] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)

    rel_obj: Any | None = None

    description: Any | str | None = None

    def get_uid(self) -> str:
        if self.uid is not None:
            return f"{self.actor_name}:{self.uid}"
        return self.actor_name

    def get_args(self) -> bytes:
        return pickle.dumps(self.args)

    def get_kwargs(self) -> bytes:
        return pickle.dumps(self.kwargs)

    def update_or_create(self):
        from authentik.tasks.schedules.models import Schedule

        query = {
            "uid": self.get_uid(),
        }
        defaults = {
            **query,
            "actor_name": self.actor_name,
            "args": self.get_args(),
            "kwargs": self.get_kwargs(),
        }
        create_defaults = {
            **defaults,
            "crontab": self.crontab,
            "rel_obj": self.rel_obj,
        }

        Schedule.objects.update_or_create(
            **query,
            defaults=defaults,
            create_defaults=create_defaults,
        )
